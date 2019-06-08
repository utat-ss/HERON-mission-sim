import numpy as n
import os.path
import datetime
import copy
import csv
import time
import visa
from modules import satellite, thermal, fileio, vis

import argparse


if __name__ == "__main__":
    

    parser = argparse.ArgumentParser(description=("tester"))
    parser.add_argument('-f', '--solar_current_file', required = True, 
                        metavar=('solar_current_file'),
                        help='.csv file containing total solar current over time, dt=1 sec')
    
    # Converts strings to objects, which are then assigned to variables below
    args = parser.parse_args()
    solar_file_path = args.solar_current_file

    supply_current_mA = []
    with open(solar_file_path, 'r') as solar_file:
        print ("Reading solar current file")
        csvreader = csv.reader(solar_file)
        line = 0
        for row in csvreader:
            if line == 0:
                print("Header row of the file: ")
                line += 1 
            else: 
                supply_current_mA.append(float(row[0]))
                line += 1
    
    print("Max current supplied: %.2f mA" % max(supply_current_mA))
    print("Min current supplied: %.2f mA" % min(supply_current_mA))

    confirmation = input("Type 'yes' to confirm that above values are nominal: ")
    if confirmation not in ['yes', '\'yes\'', 'Yes', 'YES', 'y', 'Y']:
        print("Exiting Simulation")
        input()
    
    print("Confirmed.")


    loads = [
        {'name' : 'beacon',
         'v' : 5.0,
         'i' : 1000,
         'periodic' : True,
         'constant' : False,
         'period_s' : 120,
         'length_s' : 10},

        {'name' : 'passover',
         'v' : 5.0,
         'i' : 1000,
         'periodic' : True,
         'constant' : False,
         'period_s' : 600,
         'length_s': 60},

        {'name' : 'motors',
         'v' : 5.0,
         'i' : 4000,
         'periodic' : False,
         'constant' : False,
         'onset_s' : 600,
         'length_s': 30},
    ]

    print("")
    print('*** Configure Loads ***')
    prompt = 'If you want to edit a parameter, enter its key. If not, press enter.'
    for load in loads:
        print('')
        print('###################################')
        print ("Configuring load: " + load['name'])
        print("Current configuration: ")
        print(load)
        field_to_edit = input(prompt)
        while field_to_edit is not None:
            if field_to_edit in load.keys():
                newval = input("Enter new value for " + field_to_edit)
                load[field_to_edit] = int(newval)
            else:
                print("Wrong key.")
            input(prompt)
        print ("Finished configuring " + load['name'] + ". Final config:")
        print(load)
        print('')

    
    print('')

    print('Setting up log files for this test...')
    descriptor = input('Enter short string descriptor to be added to the filename for the logs. Do not use spaces, special characters other than - and _')
    print('###################################')
    input("Press enter to begin simulation.")

    for t in range(len(supply_current_mA)):
        load_mW = 0
        for load in loads:
            if load['constant']:
                load_mW += load['i'] * load['v']
            elif load['periodic']: 
                if load['period_s'] % t < load['length_s']:
                    load_mW += load['i'] * load['v']
            else:
                if t > load['onset_s'] and t < load['onset_s'] + load['length_s']:
                    load_mW += load['i'] * load['v']

        power_requested = eload.write('POW ' + str(load_mW / 1000.0))
        current_requested = DC.write('APPL CH3, 5, ' + str(supply_current_mA[i] / 1000.0))


    



    
