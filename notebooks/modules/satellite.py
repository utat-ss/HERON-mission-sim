import copy
import csv
import numpy as n
from modules import thermal
# dt is always in seconds


class Satellite():
    def __init__(self, timings, eps, temperatures, setpoints, structure_constants):

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
        self.heater_setpoints = setpoints

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

        self.trackers = {'time' : []}
        for key in self.get_state().keys(): self.trackers[key] = []

    def update_state_tracker(self,t):
        state = self.get_state()
        for k in state.keys():
            self.trackers[k].append(copy.deepcopy(state[k]))
        self.trackers['time'].append(t)
        return state

    def get_state(self):
        loads = {}
        for load in self.loads:
            loads[load['name']] = (load['state'], load['inst_current'])
        all_state = {
            'loads': loads,
            'solar_shunts': self.solar_shunts,
            'temperatures': self.temperatures,
            'qdots': self.qdots,
            'batt_current_net': self.batt_current_net,
            'batt_current_in': self.batt_current_in,
            'batt_current_out': self.batt_current_out,
            'batt_v': self.get_battery_voltage(),
            'batt_charge': self.charge
        }
        return all_state

    def set_state(self, t):
        # dynamic state variables
        self.batt_heater['state'] = self.temperatures['battery'] < self.heater_setpoints['battery']
        self.pay_heater['state'] = self.temperatures['payload'] < self.heater_setpoints['payload']
        # time based state variables

        self.beacon['state'] = t % self.beacon_interval < self.beacon_duration
        self.exp['state'] = (t < self.exp_start_time +
                             self.exp_duration) and (t > self.exp_start_time)
        self.bus_const_pwr['state'] = True

        if self.exp['state']:
            self.passover['state'] = t % self.passover_interval < self.passover_duration_exp_on
        else:
            self.passover['state'] = t % self.passover_interval < self.passover_duration_exp_off

        if self.passover['state']:
            self.beacon['state'] = False

        if self.exp['state']:
            self.heater_setpoints['payload'] = 273.15 + 38.0

    def update_thermal(self, sun_area, zcap_sun_area, battery_discharge, dt=1.0):

        T_str = self.temperatures['structure']
        T_pay = self.temperatures['payload']
        T_bat = self.temperatures['battery']


        self.qdots['structure'] = thermal.Q_str_net(
            sun_area, T_str, T_pay, T_bat,self.structure_constants)
        self.qdots['battery'] = thermal.Q_batt_net(T_str, T_bat, self.batt_heater['state'],
                                                   battery_discharge * (dt/3600.0),self.structure_constants)
        self.qdots['payload'] = thermal.Q_pay_net(
            T_str, T_pay, self.pay_heater['state'], zcap_sun_area,self.structure_constants)



        self.temperatures['structure'] = thermal.T_str_dt(self.qdots['structure'], T_str,
                                                          T_pay, T_bat, dt,self.structure_constants)
        self.temperatures['battery'] = thermal.T_batt_dt(self.qdots['battery'], T_str,
                                                         T_bat, dt,self.structure_constants)
        self.temperatures['payload'] = thermal.T_pay_dt(self.qdots['payload'], T_str,
                                                        T_pay, dt,self.structure_constants)


    def draw_powers(self, dt=1):
        self.batt_current_out = 0
        for load in self.loads:
            if load['state']:
                load['inst_current'] = self.discharge(load['v'], load['i'], dt)
                self.batt_current_out += load['inst_current']
            else:
                load['inst_current'] = 0

        self.batt_current_net = self.batt_current_out - self.batt_current_in

    def get_battery_voltage(self):
        # replace this with actual I-V curve of the batteries
        batt_vmax = 4
        batt_vmin = 2.5
        return batt_vmin + (self.charge/(self.battery_capacity_mAh)) * (batt_vmax - batt_vmin)

    def charge_from_solar_panel(self, effective_area, dt=1.0):
        n_cells_per_side = 6.0
        # 500 is the assumed mA provided by panels in sun
        pv_cell_current_mA = 500.0 * n_cells_per_side
        new_charge = self.charge + effective_area * \
            pv_cell_current_mA * (dt/3600)
        old_charge = self.charge
        self.charge = min(new_charge, self.battery_capacity_mAh)
        if new_charge > self.battery_capacity_mAh:
            self.solar_shunts = True
        self.batt_current_in = (self.charge - old_charge) / (dt * 1.0)
        self.batt_current_net = self.batt_current_out - self.batt_current_in

    def discharge(self, voltage_out, current_out, dt=1.0):
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

