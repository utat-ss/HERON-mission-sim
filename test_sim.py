# initial set up
import numpy as n
import visa
import time
import csv
rm = visa.ResourceManager()
eload = rm.open_resource(u'USB::0x05E6::0x2380::802436012717810052::INSTR')
DC = rm.open_resource(u'USB0::0x05E6::0x2230::9104291::INSTR')
print (eload.query("*IDN?"))
print (DC.query("*IDN?"))

#start scripting:
power = eload.query_ascii_values("FETC:POW? ")


areas_in = []
with open(r'D:\Ali\Documents\UTAT\1000hr\heron_area_frac.csv','r') as csvFile:
    reader = csv.reader(csvFile)
    for row in reader:
        areas_in.append(n.float32(row[0]))

eload.write('CURR 0.01')
for i in range(len(areas_in)):
    current_ma = 500 * 3 * 1 * areas_in[i] / 1000.0

    dc_output = DC.write("APPL CH3, 5, ", str(current_ma))
    if i % 15 == 0:
        print ("Minute: ", i / 60.0)
        print ("Current (A): ", current_ma)
        print(dc_output)

    if i%60 == 1:
        print('Comms ON')
        eload.write('CURR 0.6')
    
    if i%60 == 20:
        print ("Comms OFF")
        eload.write('CURR 0.01')
    
    time.sleep(1)



