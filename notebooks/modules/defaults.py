path = '/home/ali/UTAT/mission-sim/sources/heron_area.csv'
t_orbit = 92 * 60
dt = 1
headers = ['plusX', 'plusY', 'negX', 'negY', 'plusZ', 'negZ']
panels = headers[:4]

timings = {
    'beacon_interval': 60,
    'beacon_duration':  1,
    'passover_interval': 90*60,
    'passover_duration_exp_off': 600,
    'passover_duration_exp_on': 60,
    'exp_start_time': 5 * 60 * 60,
    'exp_duration': 2 * 24 * 60 * 60
}

temperatures = {'battery': 300,
                'structure': 300,
                'payload':  300}

eps = {'battery_capacity_mAh': 20000.0,
       'converter_efficiency': 0.8,
       'starting_charge_frac': 1.0}

setpoints = {'payload_stasis': 273.15 + 30.0,
             'payload_exp': 273.15 + 38.0, 'battery': 273.15 + 30.0}

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
