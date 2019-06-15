import numpy as n
import os.path
import datetime
import copy
import csv
import time
import visa
from modules import satellite, thermal, fileio, vis
import pickle
import argparse
import datetime
from matplotlib import pyplot as plt

if __name__ == "__main__":
    

    parser = argparse.ArgumentParser(description=("tester"))
    parser.add_argument('-sf', '--solar_current_file', required = False, 
                        metavar=('solar_current_file'),
                        help='.csv file containing total solar current over time, dt=1 sec')    
    parser.add_argument('-cf', '--config_file', required = False, 
                        metavar=('config_file'),
                        help='saved configuration from a previous test')
    
    # Converts strings to objects, which are then assigned to variables below
    args = parser.parse_args()
    solar_file_path = args.solar_current_file
    config_file_path = args.config_file


    # if a config file is provided, just use that! 
    if config_file_path is not None:
        with open(config_file_path,'rb') as config_file:
            config = pickle.load(config_file)
        sim_time = config['sim_time']
        loads = config['loads']
        supply_current_mA = config['supply_current_mA']
        load_power_mW = config['load_power_mW']

    # if no config file, just do the thing
    else:
        # Set up the current supply. 
        # If file is provided, use the solar power profile from the file provided.
        # Simulation time will be equal to the length of the file provided
        # If no file is provided, you can set "phases" with set times & currents
        if solar_file_path is not None:
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
            sim_time = len(supply_current_mA)
            print("Max current supplied: %.2f mA" % max(supply_current_mA))
            print("Min current supplied: %.2f mA" % min(supply_current_mA))
            confirmation = input("Press enter to confirm that above values are nominal: ")
            if confirmation != '':
                assert False, "Simulation cancelled."
            print("Confirmed.")
        else:
            sim_time = int(input("Enter total time to simulate (in seconds): "))
            max_current_mA = 2500
            # max_current_input = input("The maximum solar current is 2500 mA by default. Enter new value if you want to change it, press enter otherwise: ")
            # if max_current_input is not None and max_current_input != '':
            #     max_current_mA = int(max_current_input)
            #     print("Max current set to %.2f mA" % max_current_input)
            phases = int(input("Enter number of different current periods to simulate: "))
            supply_current_mA = []
            for i in range(phases-1):
                print("Current Period %d: " % i)
                t_period = input("  Enter time (s): ")
                mA_period = input("  Enter current (mA): ")
                for j in range(int(t_period)): supply_current_mA.append(int(mA_period))
            print ("Current Period %d" % (phases-1))
            t_period = (sim_time - len(supply_current_mA))
            assert t_period > 0, "Too many seconds!"
            print("  Remaining time is %d s" % t_period)
            mA_Period = input("  Enter current (mA): ")
            for i in range(int(t_period)): supply_current_mA.append(int(mA_period))
        


        # Define all of the loads
        loads = [
            {'name' : 'passover',
            'enabled' : True,
            'on' : False,
            'v' : 5.0,
            'i' : 1000,
            'periodic' : True,
            'constant' : False,
            'period_s' : 600,
            'length_s': 60},

            {'name' : 'beacon',
            'enabled' : True,
            'on' : False,
            'v' : 5.0,
            'i' : 1000,
            'periodic' : True,
            'constant' : False,
            'period_s' : 120,
            'length_s' : 10},

            {'name' : 'motors',
            'enabled' : True,
            'on' : False,
            'v' : 5.0,
            'i' : 4000,
            'periodic' : False,
            'constant' : False,
            'onset_s' : 600,
            'length_s': 30},

            {'name' : 'antenna_deploy',
            'enabled' : True,
            'on' : False,
            'v' : 5.0,
            'i' : 4000,
            'periodic' : False,
            'constant' : False,
            'onset_s' : 600,
            'length_s': 30},
        ]

        # Configure each load at a time.
        print("")
        print('*** Configure Loads ***')
        prompt = '    If you want to edit a parameter, enter its key. If not, press enter: '
        for load in loads:
            print('')
            print ("Configuring load: " + load['name'])
            print("    Current configuration: ")
            for k,v in load.items():
                if k not in ['name', 'enabled', 'on']:
                    print ('        ' + str(k) + ': ' + str(v))
            print()
            # print(load)

            enable = input("    Press 'x' and enter if you want to disable this load. Press enter otherwise: ")
            if enable == 'x':
                load['enabled'] = False
            else:
                load['enabled'] = True
                field_to_edit = input(prompt)
                while field_to_edit != '':
                    if field_to_edit in load.keys():
                        newval = input("        Enter new value for " + field_to_edit + ': ')
                        load[field_to_edit] = float(newval)
                    else:
                        print("      Wrong key.")
                    field_to_edit = input(prompt)


            print ("Finished configuring " + load['name'] + ". Final config:")
            print(load)
            print('')


        print('')


        # Calculate the power from each load at any second
        load_power_mW = []
        for t in range(sim_time):
            load_mW = 0
            # print("\n Time is %d" % t)
            for load in loads:
                if load['enabled']:
                    if load['constant']:
                        # print(load['name'] + 'is on')
                        load_mW += load['i'] * load['v']
                    elif load['periodic']: 
                        if (t % load['period_s']) < load['length_s']:
                            # print(load['name'] + 'is on')
                            load_mW += load['i'] * load['v']
                    else:
                        if t > load['onset_s'] and t < load['onset_s'] + load['length_s']:
                            # print(load['name'] + 'is on')
                            load_mW += load['i'] * load['v']
            load_power_mW.append(load_mW)

    fig, ax1 = plt.subplots()
    ln1 = ax1.plot(range(sim_time), load_power_mW, label='Power Out (mW)', color='red')
    ax2 = ax1.twinx()
    ln2 = ax2.plot(range(sim_time), supply_current_mA, label='Current In (mA)', color='blue')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel("Power (mW)")
    ax2.set_ylabel("Current (mW)")
    lns = ln1+ln2 
    lbs = [l.get_label() for l in lns]
    ax1.legend(lns, lbs)
    plt.title("Load to simulate. Exit to continue.")
    plt.show()
    # time.sleep(1)


    print('Setting up log files for this test...')
    descriptor = input('Enter short string descriptor to be added to the filename for the logs. Do not use spaces, special characters other than - and _')
    
    now = str(datetime.datetime.now())
    path = 'logs/'
    filename_prefix = path + 'log-' + descriptor + '-' + now[2:10] + '--' + now[11:13] + '-' + now[14:16] + '-' + now[17:19]
    with open(filename_prefix + '-config.pickle', 'wb') as f:
        pickle.dump({'loads' : loads, 'sim_time' : sim_time, 'load_power_mW' : load_power_mW, 'supply_current_mA' : supply_current_mA}, f)
    with open(filename_prefix + '-plot.png', 'wb') as f:
        fig.savefig(f)
    datafile = filename_prefix + '-data.csv'


    rm = visa.ResourceManager()
    
    print("Connecting to DC Power Supply")
    DC = rm.open_resource(u'USB0::0x05E6::0x2230::9104291::INSTR')
    print ("DC Supply Connected. Device ID:")
    print (DC.query("*IDN?"))

    print ("Connecting to Eload")
    eload = rm.open_resource(u'USB::0x05E6::0x2380::802436012717810052::INSTR')
    print ("ELoad Connected. Device ID: ")
    print (eload.query("*IDN?"))


    input("Enter to start sim.\n")
    with open(datafile, 'w') as f:
        writer = csv.writer(f,lineterminator = '\n')
        for t in range(sim_time):
            power_requested = eload.write('POW ' + str(load_power_mW[t] / 1000.0))
            current_requested = DC.write('APPL CH1, 5, ' + str(supply_current_mA[t] / 1000.0))

            writer.writerow(  [float(load_power_mW[t]), float(supply_current_mA[t])]  )
            time.sleep(1)

    



    
