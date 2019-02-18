import numpy as n
from geometry import *
from vpython import canvas, sphere, box, local_light, color

def make_orbit_scene(solar_sys, satellite, altitude, flipper):

    rsun = solar_sys['sun_radius']
    rearth = solar_sys['earth_radius']
    psun = (0, solar_sys['sun_dist'], 0)
    pearth = (0, 0, 0)

    psat = (0, 0, rearth+altitude)
    size_sat = satellite['sizefactor']
    up_sat = satellite['up_vector']

    scene = canvas()
    sun = sphere(pos=vecflip(psun, flipper), radius=rsun,
                 emissive=True, color=color.yellow)
    earth = sphere(pos=vecflip(pearth, flipper), radius=rearth,
                   color=color.green, make_trail=False)
    scene.lights = []
    sunlight = local_light(pos=vecflip(psun, flipper), color=color.gray(0.4))
    scene.ambient = color.gray(0.5)
    sat = box(pos=vecflip(psat, flipper), length=0.1*size_sat, width=0.1*size_sat,
              height=0.3*size_sat, up=vecflip(up_sat, flipper), make_trail=True)

    solar_sys['sun'] = sun
    solar_sys['earth'] = earth
    satellite['sat'] = sat

    return scene, solar_sys, satellite


def make_view_scene(solar_sys, satellite, flipper):

    psun = (0, solar_sys['sun_dist'], 0)
    up_sat = satellite['up_vector']

    sat_view_scene = canvas()
    sat_view = box(pos=vecflip((0, 0, 0), flip=flipper),  width=0.1,
                   length=0.1, height=0.3, up=vecflip(up_sat), make_trail=True)
    sat_view_scene.lights = []
    sat_view_scene.ambient = color.gray(0.3)
    sun_view = local_light(pos=vecflip(
        psun,  flip=flipper), color=color.gray(0.4))
    # sat_view.axis = vecflip(sat_axis)

    solar_sys['sun_v'] = sun_view
    satellite['sat_v'] = sat_view

    return sat_view_scene, solar_sys, satellite


def animate(solar_sys, satellite, orbit, t, dt, flip_o, flip_v):
    new_pos = orbit_xyz(t, orbit['theta'], orbit['phi']) * \
        (solar_sys['earth_radius'] + orbit['altitude'])
    satellite['sat'].pos = vecflip(new_pos, flip_o)

    new_psi = get_psi(t, orbit['psi_mode'])
    new_up = orbit_xyz(new_psi/(2*n.pi), orbit['theta'], orbit['phi'])
    satellite['sat'].up = vecflip(new_up, flip_o)

    satellite['sat'].rotate(angle=get_zrot(
        dt/orbit['zrot_period']), axis=satellite['sat'].up)

    satellite['sat_v'].up = vecflip(new_up, flip=flip_v)

    if t < 0.5:
        solar_sys['sun_v'].color = color.gray(0)
    else:
        solar_sys['sun_v'].color = color.gray(0.6)
