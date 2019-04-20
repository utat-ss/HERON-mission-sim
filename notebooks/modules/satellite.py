import copy
import csv
import numpy as n

# uncomment if in notebook
# from modules import thermal

# uncomment if not in notebook
import thermal

# dt is always in seconds


class Satellite():
    def __init__(self, timings, eps, temperatures, setpoints, structure_constants):
        """
        Create a new satellite object with the given properties and initial state. 
        The format of the dictionaries is important, so please refer to the main notebook to see what they should contain

        Arguments:
            timings {dict} -- frequency, length, start/end times of different loads
            eps {dict} -- characteristics of the power system
            temperatures {dict} -- starting temperatures of structure, payload and battery
            setpoints {dict} -- heater setpoints for battery & payload heaters
            structure_constants {dict} -- structural constants affecting thermal simulations
        """

        # Initialize power systems
        self.battery_capacity_mAh = eps['battery_capacity_mAh']
        self.converter_efficiency = eps['converter_efficiency']
        self.charge = self.battery_capacity_mAh * eps['starting_charge_frac']
        self.solar_shunts = False

        self.structure_constants = copy.deepcopy(structure_constants)

        # Setup mission timings
        self.beacon_interval = timings['beacon_interval']
        self.beacon_duration = timings['beacon_duration']
        self.passover_interval = timings['passover_interval']
        self.passover_duration_exp_off = timings['passover_duration_exp_off']
        self.passover_duration_exp_on = timings['passover_duration_exp_on']
        self.exp_start_time = timings['exp_start_time']
        self.exp_duration = timings['exp_duration']
        self.heater_setpoints = copy.deepcopy(setpoints)

        # Initialize Thermal
        self.temperatures = copy.deepcopy(temperatures)
        self.qdots = {'battery': 0, 'structure': 0, 'payload': 0}

        # create the loads
        self.beacon = {'state': False, 'i': 1000,
                       'v': 5.0, 'name': 'Beacon', 'inst_current': 0}
        self.passover = {'state': False, 'i': 1000,
                         'v': 5.0, 'name': 'Passover', 'inst_current': 0}
        self.exp = {'state': False, 'i': 100,   'v': 3.3,
                    'name': 'Experiment', 'inst_current': 0}
        self.batt_heater = {'state': False, 'i': 250,
                            'v': 5.0, 'name': 'Battery Heater', 'inst_current': 0}
        self.pay_heater = {'state': False, 'i': 500,
                           'v': 5.0, 'name': 'Payload Heater', 'inst_current': 0}
        self.bus_const_pwr = {'state': False, 'i': 200,
                              'v': 3.3, 'name': 'Bus', 'inst_current': 0}

        self.loads = [self.exp, self.bus_const_pwr, self.beacon,
                      self.passover, self.batt_heater, self.pay_heater]

        # unit is in mA
        self.batt_current_in = 0
        self.batt_current_out = 0
        self.batt_current_net = self.batt_current_out - self.batt_current_in

        # the trackers dictionary contains all of the data needed
        self.trackers = {'time': []}
        for key in self.get_state().keys():
            self.trackers[key] = []

    def update_state_tracker(self, t):
        '''
        Updates the internal state tracker of the Satellite object with the current state.
        Can be called at each iteration to record the current status. 

        Arguments:
            t {float} -- Current time of the simulation to timestamp the state

        Returns:
            dict -- dictionary containing all state variables
        '''

        state = self.get_state()
        for k in state.keys():
            self.trackers[k].append(copy.deepcopy(state[k]))
        self.trackers['time'].append(t)
        return state

    def get_state(self):
        '''
        Read the state variable and compile them in a dictionary for easy access

        Returns:
            dict -- the current state of the satellite, including all of the loads, temperatures, powers, etc.
        '''

        loads = {}
        for load in self.loads:
            loads[load['name']] = (int(load['state']), load['inst_current'])
        batt_v = self.get_battery_voltage()
        all_state = {
            'loads': loads,
            'solar_shunts': self.solar_shunts,
            'temperatures': self.temperatures,
            'qdots': self.qdots,
            'batt_current_net': self.batt_current_net,
            'batt_current_in': self.batt_current_in,
            'batt_current_out': self.batt_current_out,
            'batt_v': batt_v,
            'batt_charge': self.charge,
            'power_in': self.batt_current_in * batt_v,
            'power_out': self.batt_current_out * batt_v,
            'power_net': - self.batt_current_net * batt_v,
        }
        return all_state

    def set_state(self, t):
        '''
        Determine the on/off status of loads given the current time, and write the status to the state variables of the Satellite object

        Arguments:
            t {float} -- current time (in seconds) of the simulation
        '''

        # Dynamic State Variables
        # Determine which pay_setpoint to use depending on the experiment state
        pay_setpoint = self.heater_setpoints['payload_exp'] if self.exp['state'] else self.heater_setpoints['payload_stasis']
        # Determine whether the heaters should be on given the current temperatures
        self.batt_heater['state'] = self.temperatures['battery'] < self.heater_setpoints['battery']
        self.pay_heater['state'] = self.temperatures['payload'] < pay_setpoint

        # Time-based variables
        self.beacon['state'] = t % self.beacon_interval < self.beacon_duration
        self.exp['state'] = (t < self.exp_start_time +
                             self.exp_duration) and (t > self.exp_start_time)

        # The bus is always on
        self.bus_const_pwr['state'] = True

        # If the experiment is running, use the short passover time, use the long one otherwise
        if self.exp['state']:
            self.passover['state'] = t % self.passover_interval < self.passover_duration_exp_on
        else:
            self.passover['state'] = t % self.passover_interval < self.passover_duration_exp_off

        # If we are in a passover, override the beacon and set it false
        if self.passover['state']:
            self.beacon['state'] = False

    def update_thermal(self, sun_area, zcap_sun_area, battery_discharge, dt=1.0):
        '''
        Given the current state of the satellite, update the Qdots and the temperatures.
        Uses numerical methods to time-step through the thermal equations.

        Arguments:
            sun_area {float} -- the total projected surface area (m^2) of the satellite exposed to the sun
            zcap_sun_area {float} -- the total projected surface area (m^2) of the payload bottom cap exposed to the sun
            battery_discharge {float} -- net current (mA) OUT of the battery to calculate self-heating

        Keyword Arguments:
            dt {float} -- Time step of the simulation (secods) (default: {1.0})
        '''

        # Load the current temperatures
        T_str = self.temperatures['structure']
        T_pay = self.temperatures['payload']
        T_bat = self.temperatures['battery']

        # Update the Q-dots of the satellite
        self.qdots['structure'] = thermal.Q_str_net(
            sun_area, T_str, T_pay, T_bat, self.structure_constants)
        self.qdots['battery'] = thermal.Q_batt_net(T_str, T_bat, self.batt_heater['state'],
                                                   battery_discharge * (dt/3600.0), self.structure_constants)
        self.qdots['payload'] = thermal.Q_pay_net(
            T_str, T_pay, self.pay_heater['state'], zcap_sun_area, self.structure_constants)

        # Update the temperatures
        self.temperatures['structure'] = thermal.T_str_dt(self.qdots['structure'], T_str,
                                                          T_pay, T_bat, dt, self.structure_constants)
        self.temperatures['battery'] = thermal.T_batt_dt(self.qdots['battery'], T_str,
                                                         T_bat, dt, self.structure_constants)
        self.temperatures['payload'] = thermal.T_pay_dt(self.qdots['payload'], T_str,
                                                        T_pay, dt, self.structure_constants)

    def draw_powers(self, dt=1.0):
        """
        Loops through all of the loads and drains the battery according to the current state of each load.

        Keyword Arguments:
            dt {float} -- Time step (seconds) (default: {1.0})
        """

        self.batt_current_out = 0
        for load in self.loads:
            if load['state']:
                load['inst_current'] = self.discharge(load['v'], load['i'], dt)
                self.batt_current_out += load['inst_current']
            else:
                load['inst_current'] = 0

        self.batt_current_net = self.batt_current_out - self.batt_current_in

    def get_battery_voltage(self):
        '''
        Calculate the battery voltage depending on the current charge of the battery.
        This model can be expanded to include voltage inflation or sagging, as well as the non-linear chrage/voltage curve, but for now it is a linear model.

        Returns:
            float -- battery voltage (V)
        '''

        # replace this with actual I-V curve of the batteries
        batt_vmax = 4
        batt_vmin = 2.5
        return batt_vmin + (self.charge/(self.battery_capacity_mAh)) * (batt_vmax - batt_vmin)

    def charge_from_solar_panel(self, effective_area, dt=1.0):
        """
        Charge the batteries from the solar panels.
        Charges only up to the maximum capacity of the batteries, and turns on shunts if that is exceeded

        Arguments:
            effective_area {float} -- projected solar panel area exposed to the sun, expressed as a fraction of 1 side. 1.0 means one side is directly in sun, and maximum is 1.41 to account for sun at the corner.        
        Keyword Arguments:
            dt {float} -- Simulation time step (seconds) (default: {1.0})
        """

        n_cells_per_side = 3.0  # 3 because we have 3 sets of 2 in series
        # 500 is the assumed mA provided by panels in sun
        pv_cell_current_mA = 500.0 * n_cells_per_side
        # assume that charge is linear with area
        new_charge = self.charge + effective_area * \
            pv_cell_current_mA * (dt/3600)

        # Add to the battery, making sure we don't overcharge
        self.batt_current_in = ((min(new_charge, self.battery_capacity_mAh)) - self.charge) / (dt * 1.0 / 3600.0)
        self.charge = min(new_charge, self.battery_capacity_mAh)
        if new_charge > self.battery_capacity_mAh:
            self.solar_shunts = True
        self.batt_current_net = self.batt_current_out - self.batt_current_in

    def discharge(self, voltage_out, current_out, dt=1.0):
        '''
        Discharge the battery with the given load parameters.
        Accounts for the boost/downstepping of current based on inputs, and the converter losses.

        Arguments:
            voltage_out {float} -- The voltage of the load (V)
            current_out {float} -- The current drawn by load (mA)

        Keyword Arguments:
            dt {float} -- Time step of simulation (seconds) (default: {1.0})

        Returns:
            float -- current out (mA)
        '''

        newcharge = self.charge - ((voltage_out * current_out)/self.get_battery_voltage()) * (
            dt / 3600.0) * (1/self.converter_efficiency)
        delta = newcharge - self.charge
        #         print (self.charge, newcharge)?
        if newcharge < 0:
            print("Battery Died")
            self.charge = 0
        else:
            self.charge = newcharge

        return current_out
