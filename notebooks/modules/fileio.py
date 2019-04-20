import numpy as n
import csv

def read_areas_from_file(path, dt, t_orbit=None, headers=['plusX', 'plusY', 'negX', 'negY', 'plusZ', 'negZ']):
    """
    Reads in the projected sun-facing areas of each face of the satellite over time from a csv file.
    The csv file can be generated through STK. It has N*(M+1) + 2 rows, where N is the number of time points and M is the number of faces.
    The first row is the title row, and its index-1 element is assumed to be 'Time'. The final row is a row of four null characters.
    There are M sections, each section starts with a row containing the header, followed by N rows containint (time, area).
    The units of area is m^2, and the time is in a datetime format.

    Arguments:
        path {string} -- Absolute path to source csv file
        dt {float} -- Time step of the simulation seconds
    
    Keyword Arguments:
        t_orbit {integer} -- The length of the orbit in seconds. If this is greater than the number of rows, the output is padded with 0-rows until this length is met (default: {None})
        headers {list} -- The names of the headers for each face (default: {['plusX', 'plusY', 'negX', 'negY', 'plusZ', 'negZ']})
    
    Returns:
        [np.array] -- Structured numpy array with a field for each header, and N elements under each header.
    """



    # if t_orbit > len(file)*dt, it will be padded with 0s
    areas_dict = {}
    
    
    with open(path, encoding='utf-8') as area_csv_file:
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
