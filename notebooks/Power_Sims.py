import numpy as n
import os.path
import datetime

from imp import reload
import copy
import csv
import time

from modules import satellite, thermal, fileio, vis

t_orbit = 92 * 60
dt = 1
path = '/home/ali/UTAT/mission-sim/sources/heron_area.csv'
headers = ['plusX','plusY','negX','negY', 'plusZ', 'negZ']
panels = headers[:4]

areas = fileio.read_areas_from_file(path, dt, t_orbit)
total_areas = areas['plusX'] - areas['plusX']
panel_areas = total_areas.copy()
for h in headers:
    total_areas += areas[h]
    if h in panels: panel_areas += areas[h]
n_pts_per_orbit = len(areas)

timings = {
    'beacon_interval' : 60,
    'beacon_duration' :  1,
    'passover_interval' : 90*60,
    'passover_duration_exp_off' : 600,
    'passover_duration_exp_on' : 60,
    'exp_start_time' : 5  * 60 * 60,
    'exp_duration' : 2 * 24 * 60 * 60
}

temperatures = {'battery': 300,2
                'structure': 300,
                'payload':  300}

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

heron = satellite.Satellite(timings,eps, temperatures, setpoints, structure_constants)

heron.get_battery_voltage()

n_orbits = 3
n_points = n_orbits * n_pts_per_orbit
t_sim = n_points * dt

powerIn = []
powerOut = []
for i in range(n_points):
    heron.set_state(i)
    heron.draw_powers()
    heron.update_thermal(total_areas[i % len(areas)], areas['negZ'][i%len(areas)], heron.batt_current_net)
    heron.charge_from_solar_panel(panel_areas[i % len(areas)] / (0.03 * 0.01), dt)
    heron.update_state_tracker(i*dt)
    powerIn.append(heron.power_in)
    powerOut.append(heron.power_out)

#for actual DC supply / Eload code.

rm = visa.ResourceManager()
eload = rm.open_resource(u'USB::0x05E6::0x2380::802436012717810052::INSTR')
DC = rm.open_resource(u'USB0::0x05E6::0x2230::9104291::INSTR')
print (eload.query("*IDN?"))
print (DC.query("*IDN?"))

#start scripting:
power = eload.query_ascii_values("FETC:POW? ")

for i in range(len(powerIn)):
    powerIn_watts = eload.write('POW', str(powerIn[i]))
for i in range(len(powerOut)):
    powerOut_watts = DC.write('POW', str( powerOut[i]))





#Step 1: obtaining power from
# areas_in = []
# with open(r'D:\Ali\Documents\UTAT\1000hr\heron_area_frac.csv','r') as csvFile:
#     reader = csv.reader(csvFile)
#     for row in reader:
#         areas_in.append(n.float32(row[0]))
#
# eload.write('CURR 0.01')
# for i in range(len(areas_in)):
#     current_ma = 500 * 3 * 1 * areas_in[i] / 1000.0
#
#     dc_output = DC.write("APPL CH3, 5, ", str(current_ma))
#     if i % 15 == 0:
#         print ("Minute: ", i / 60.0)
#         print ("Current (A): ", current_ma)
#         print(dc_output)
#
#     if i%60 == 1:
#         print('Comms ON')
#         eload.write('CURR 0.6')
#
#     if i%60 == 20:
#         print ("Comms OFF")
#         eload.write('CURR 0.01')
#
#     time.sleep(1)
