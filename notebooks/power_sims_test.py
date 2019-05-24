import numpy as n
import os.path
import datetime

from imp import reload
import copy
import csv
import time

import visa

import satellite, thermal, fileio, vis
#from module import satellite, thermal, fileio, vis

t_orbit = 92 * 60
dt = 1
path = '.\heron_area.csv' #changes for person
headers = ['plusX','plusY','negX','negY', 'plusZ', 'negZ']
panels = headers[:4] # python list

#This part of the code reads heron_area.csv
#t_orbit / dt is the number of rows we are reading i think
areas = fileio.read_areas_from_file(path, dt, t_orbit)
total_areas = areas['plusX'] - areas['plusX'] #this is some dumb trick, dont worry about it
panel_areas = total_areas.copy()

# total area = plusX + plusY + negX + negY + plusZ + negZ
#area is from the CSV files
#so we're reading the csv file
for h in headers:
        total_areas += areas[h]
        if h in panels: panel_areas += areas[h]
n_pts_per_orbit = len(areas)

#these are parameters for a dictonary which will be read
#in the Satellite constructor:

#please note that all units for time are in seconds:
timings = {
        'beacon_interval': 60,
        'beacon_duration': 1,
        'passover_interval' : 90*60,
        'passover_duration_exp_off' : 600,
        'passover_duration_exp_on' : 60,
        'exp_start_time' : 5  * 60 * 60,
        'exp_duration' : 2 * 24 * 60 * 60
}

#Temperaturea
temperatures = {'battery': 300,
                'structure': 300,
                'payload':  300}

#Battery stuff
eps = {'battery_capacity_mAh' : 20000.0,
       'converter_efficiency' : 0.8,
       'starting_charge_frac' : 1.0}

setpoints = {'payload_stasis': 273.15 + 30.0, 'payload_exp': 273.15 + 38.0,'battery': 273.15 + 30.0}

structure_constants = {
    'area_t': 0.0013,  # total surface area of sat
    'r_batt': 130 * 10**-3,  # ohm,s #for self heating
    'R_str_pay': 16.67,  # K/W
    'R_str_batt': 14,  # fake
    'c_str': 900,  # estimate (J/K)
    'c_batt': 850,  # estimate (J/K)
    'c_pay': 800,  # guess (J/K)
    'e': 0.58,  # sat emissivity
    'a': 0.72,  # sat absorbtivity
}

#now foe creating the actual object:
heron = satellite.Satellite(timings,eps, temperatures, setpoints, structure_constants)

heron.get_battery_voltage()

n_orbits = 3
n_points = n_orbits * n_pts_per_orbit
t_sim = n_points * dt

#power going out of the batt
powerOutBatt = []

#Power going into the batt
powerToBatt = []
voltageBatt = []
currentBatt = []

for i in range(n_points):
    heron.set_state(i)
    heron.draw_powers()
    heron.update_thermal(total_areas[i % len(areas)], areas['negZ'][i%len(areas)], heron.batt_current_net)
    heron.charge_from_solar_panel(panel_areas[i % len(areas)] / (0.03 * 0.01), dt)
    heron.update_state_tracker(i*dt)

    # The Eload will take this value
    powerOutBatt.append((heron.get_state()['power_out']) / 1000)

    # The DC power supply will take this value
    voltageBatt.append((heron.get_state()['batt_v']))
    currentBatt.append((heron.get_state()['batt_current_in']) / 1000)
    powerToBatt.append(n.multiply(voltageBatt[i], currentBatt[i]))

print("sanity check of the lengths: ")
print(len(powerOutBatt))
print(len(powerToBatt))

#for actual DC supply / Eload code
#UNCOMMENT WHEN TESTING WITH THE ELOAD / POWER SUPPLY

rm = visa.ResourceManager()
eload = rm.open_resource(u'USB::0x05E6::0x2380::802436012717810052::INSTR')
DC = rm.open_resource(u'USB0::0x05E6::0x2230::9104291::INSTR')
print (eload.query("*IDN?"))
print (DC.query("*IDN?"))

#start scripting:
power = eload.query_ascii_values("FETC:POW? ")

# lmao don't worry they are of the same length
for i in range(len(powerOutBatt)):
    if powerOutBatt[i] != 0: #I was testing, irl remove this condition

        #eload requesting the power
        powerRequested = eload.write('POW ' + str(powerOutBatt[i]))
        #DC supply providing the power
        powerIntoBatt = DC.write('APPL CH3, ' + str(voltageBatt[i]) + ', ' + str(currentBatt[i]))

        print("Parameters: ")
        print('APPL CH3, ' + str(voltageBatt[i]) + ', ' + str(currentBatt[i]))
        print('Power into the battery:' + str(powerToBatt[i]))
        print('Power out of the battery:' + str(powerOutBatt[i]))
        print(' ')
        time.sleep(0.1) #change depending on how fast you want to simluation to be

