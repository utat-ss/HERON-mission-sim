import numpy as n
import csv

def read_areas_from_file(path, dt, t_orbit=None, headers=['plusX', 'plusY', 'negX', 'negY', 'plusZ', 'negZ']):
    # if t_orbit > len(file)*dt, it will be padded with 0s
    areas_dict = {}
    with open(path) as area_csv_file:
        reader = csv.reader(area_csv_file)
        for row in reader:
            if row[0] in headers:
                areas_dict[row[0]] = {'times': [], 'area': [], 'intensity': []}
                current_header = row[0]
            elif row[1] == 'Time':
                continue
            elif row == ['', '', '', '', '']:
                break
            else:
                areas_dict[current_header]['times'].append((row[2]))
    #             print('value:',  row[3])
                areas_dict[current_header]['area'].append(n.float32(row[3]))
                areas_dict[current_header]['intensity'].append(
                    n.float32(row[4]))

    areas = n.array(n.zeros(int(t_orbit/dt)),
                     [(h, n.float32) for h in headers])
    for h in headers:
        areas[h][:len(areas_dict[h]['area'])] = n.array(
            areas_dict[h]['area'])*0.01
    times = n.array([i*dt for i in range(int(t_orbit/dt))], n.float32)
    return areas
