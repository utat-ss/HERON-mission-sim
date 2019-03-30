import numpy as n
from geometry import *
from vpython import canvas, sphere, box, local_light, color, rate

def make_orbit_scene(solar_sys, satellite):

    rsun = solar_sys['sun_radius']
    rearth = solar_sys['earth_radius']
    psun = solar_sys['sun_dist'] * n.array(solar_sys['sun_vector'])
    pearth = (0, 0, 0)
    altitude = satellite.orbit['altitude']

    psat = (0, 0, rearth+altitude)
    size_sat = satellite.properties['sizefactor']
    up_sat = satellite.starting_orientation[4]

    scene = canvas()
    sun = sphere(pos=vecflip(psun, solar_sys['flip_o']), radius=rsun,
                 emissive=True, color=color.yellow)
    earth = sphere(pos=vecflip(pearth, solar_sys['flip_o']), radius=rearth,
                   color=color.green, make_trail=False)
    scene.lights = []
    sunlight = local_light(pos=vecflip(psun, solar_sys['flip_o']), color=color.gray(0.4))
    scene.ambient = color.gray(0.5)
    sat = box(pos=vecflip(psat, solar_sys['flip_o']), length=0.1*size_sat, width=0.1*size_sat,
              height=0.3*size_sat, up=vecflip(up_sat, solar_sys['flip_o']), make_trail=True)

    solar_sys['sun'] = sun
    solar_sys['earth'] = earth
    satellite.sat3d = sat

    satellite.zrot = 0

    return scene, solar_sys, satellite


def make_view_scene(solar_sys, satellite):

    psun = (0, solar_sys['sun_dist'], 0)
    up_sat = satellite.starting_orientation[4]

    sat_view_scene = canvas()
    sat_view = box(pos=vecflip((0, 0, 0), flip=solar_sys['flip_v']),  width=0.1,
                   length=0.1, height=0.3, up=vecflip(up_sat), make_trail=True)
    sat_view_scene.lights = []
    sat_view_scene.ambient = color.gray(0.3)
    sun_view = local_light(pos=vecflip(
        psun,  flip=solar_sys['flip_v']), color=color.gray(0.4))
    # sat_view.axis = vecflip(sat_axis)

    solar_sys['sun_v'] = sun_view
    satellite.sat_v3d = sat_view

    return sat_view_scene, solar_sys, satellite


def animate(solar_sys, satellite, t, dt, curves, point):
    orbit = satellite.orbit
    new_pos = orbit_xyz(t, orbit['theta'], orbit['phi']) * \
        (solar_sys['earth_radius'] + orbit['altitude'])
    satellite.sat3d.pos = vecflip(new_pos, solar_sys['flip_o'])

    new_psi = get_psi(t, orbit['psi_mode'])
    new_up = rotate_vector((0,0,1), orbit['theta'], orbit['phi'], new_psi)
    satellite.sat3d.up = vecflip(new_up, solar_sys['flip_o'])

    satellite.zrot = (satellite.zrot + get_zrot(dt/orbit['zrot_period'])) % (2*n.pi)
    satellite.sat3d.rotate(angle=get_zrot(
        dt/orbit['zrot_period']), axis=satellite.sat3d.up)

    satellite.sat_v3d.up = vecflip(new_up, flip=solar_sys['flip_v'], signs=(-1,1,1))

    # https://ocw.mit.edu/courses/aeronautics-and-astronautics/16-851-satellite-engineering-fall-2003/projects/portfolio_nadir1.pdf
    eclipse_frac = 0.5

    total_power_gen = 0
    for i in range(satellite.starting_orientation.shape[0]):
        satellite.current_orientation[i] = rotate_vector(satellite.starting_orientation[i],orbit['theta'],orbit['phi'], new_psi )
        satellite.area_ratio[i], satellite.normal_angles[i] = dot_and_angle(solar_sys['sun_vector'], satellite.current_orientation[i])
        
        power_gen = -1.0 * solar_sys['solar_flux'] * (1/10000.0) * satellite.cell_areas[i] * 0.3 * satellite.area_ratio[i]
        if power_gen < 0 or t < eclipse_frac: power_gen = 0
        total_power_gen += power_gen
        curves[i].plot([point*dt, power_gen])
        satellite.gen_powers_per_face[i, point] = power_gen
            
    curves[6].plot(point*dt, total_power_gen)
    
    
    # print(new_up)
    # print (satellite.area_ratio)
    # print (satellite.normal_angles)
    # print (satellite.current_orientation)

    # equation here to determine true eclipse frac
    if t < eclipse_frac:
        solar_sys['sun_v'].color = color.gray(0)
    else:
        solar_sys['sun_v'].color = color.gray(0.6)


def simulate(sim_props, satellite, solar_system, area_curves, graph):
    orbit = satellite.orbit
    dt = sim_props['dt']
    sim_time = sim_props['sim_time']
    total_time = sim_props.get('total_time', None)
    n_orbits = sim_props.get('n_orbits', None)

    satellite.sat_v3d.axis = vecflip((0.1,0,0), flip=solar_system['flip_v'], signs=(-1,1,1))
    
    n_pts_per_orbit = n.int(orbit['period'] / dt)
    if n_pts_per_orbit * dt !=   orbit['period']:
        dt = orbit['period'] / (1.0*n_pts_per_orbit)
        print("Changing dt to %.2f" % dt)

    if total_time is not None:
        n_orbits = n.floor(total_time / orbit['period'])
    if total_time != orbit['period'] * n_orbits:
        total_time = orbit['period'] * n_orbits
        print("Changing total time simulated to %.2f" % total_time)

    n_pts = n_pts_per_orbit * n_orbits + 1
    satellite.gen_powers_per_face = n.zeros((7, n_pts),n.float32)
    satellite.ts = n.zeros(n_pts, n.float32)
    # at this point, n_pts_per_orbit and n_pts are integers

    for i in range(n_pts):
        
        t = i * dt
        fraction_orbit = (t % orbit['period'])/orbit['periokeybd']
        satellite.ts[i] = i
        animate(solar_system, satellite, fraction_orbit,
                dt, area_curves, i)
        rate(n_pts / sim_props['sim_time'])

        if t > 299:
            graph.xmax = t
            graph.xmin = t - 300
