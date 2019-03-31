import numpy as n
from geometry import *
from vpython_utils import *
from vpython import *

solar_sys = {'sun_dist': 50e6,
             'sun_radius': 20e6,
             'earth_radius': 6.371e6}
orbit = {'period': 90,
         'altitude': 10e5,
         'phi': n.pi/2,
         'theta': 0,
         'zrot_period': 1,
         'psi_mode': 'linear'}

satellite = {'up_vector': (0, 0, 1),
             'sizefactor': 5e6}

flip_o = [1, 2, 0]
flip_v = [0, 2, 1]


if __name__ == '__main__':
    sc, solar_sys, satellite = make_orbit_scene(solar_sys, satellite, orbit['altitude'], flip_o)

    sc_v, solar_sys, satellite = make_view_scene(solar_sys, satellite, flip_v)

    satellite['sat'].clear_trail()
    orbit['theta'] = 0
    orbit['phi'] = 0
    orbit['zrot_period'] = 1

    n_points = 200  # number of simulation points per orbit

    simtime = 5  # secs, simulation time of a single orbit
    number_of_orbits = 1  # number of orbits to simulate

    dt = orbit['period'] / (1.0 * n_points)

    for i in linspace(0, number_of_orbits*orbit['period'], number_of_orbits*n_points):
        rate(n_points/simtime)
        t = (i % orbit['period'])*1.0/orbit['period']

        animate(solar_sys, satellite, orbit, t, dt, flip_o, flip_v)
