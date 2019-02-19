import numpy as n

from vpython import vector


def get_psi(t, method='fast-pole-flip'):
    if method not in ['fast-pole-flip', 'slow-pole-flip', 'linear', 'zero']:
        print("Invalid method, default to linear")

    #if method == 'linear':
    theta = (4 * n.pi * t)
    if method == 'slow-pole-flip':
        theta -= n.sin(4*n.pi*t)
    elif method == 'fast-pole-flip':
        theta += n.sin(4*n.pi*t)
    elif method == 'zero':
        theta = 0

    return theta % (2*n.pi)


def get_zrot(t):
    # note that this t is not in the same scale as the ts above
    # this t is time_slice / period_zrot
    # other ts are curr_time / period
    # returns the amount of rotation
    # for a constant rate of rotation it will return a constant
    return 2*n.pi * t

def rotate_vector(v, theta = 0, phi = 0, psi=0):
    v = n.array(v).reshape(3)
    rot_matrix_d = n.array([[n.cos(phi), n.sin(phi), 0],
                            [-n.sin(phi), n.cos(phi), 0],
                            [0, 0, 1]])

    rot_matrix_c = n.array([[1, 0, 0],
                            [0, n.cos(theta), n.sin(theta)],
                            [0, -n.sin(theta), n.cos(theta)]])

    rot_matrix_b = n.array([[n.cos(psi), n.sin(psi),0],\
                            [-n.sin(psi), n.cos(psi), 0],\
                            [0, 0, 1]])

    rot_matrix_cb = n.matmul(rot_matrix_c, rot_matrix_b)
    rot_matrix_dcb = n.matmul(rot_matrix_d, rot_matrix_cb)
    # print (rot_matrix_cb)
#     rot_matrix = n.matmul(rot_matrix_b, rot_matrix_cd)

    return n.matmul(rot_matrix_dcb, v.T)


def orbit_xyz(t,  # time elapsed / period, 0 < t < 1
              theta=0,
              phi=0,
              psi=0
              ):

    base_orbit = n.array([n.sin(t*2*n.pi), 0, n.cos(t*2*n.pi)])

    rot_matrix_d = n.array([[n.cos(phi), n.sin(phi), 0],
                            [-n.sin(phi), n.cos(phi), 0],
                            [0, 0, 1]])

    rot_matrix_c = n.array([[1, 0, 0],
                            [0, n.cos(theta), n.sin(theta)],
                            [0, -n.sin(theta), n.cos(theta)]])

#     rot_matrix_b = n.array([[n.cos(psi), n.sin(psi),0],\
#                             [-n.sin(psi), n.cos(psi), 0],\
#                             [0, 0, 1]])

    rot_matrix_cd = n.matmul(rot_matrix_d, rot_matrix_c)
#     rot_matrix = n.matmul(rot_matrix_b, rot_matrix_cd)

    rotated_orbit = n.matmul(rot_matrix_cd, base_orbit.T)

    return rotated_orbit
# def orbit_xyz(t,  # time elapsed / period, 0 < t < 1
#               theta=0,
#               phi=0,
#               axis_0 = 0,
#               axis_1 = 2, 
#               free_axis = 1
#               ):
#     base_orbit = n.zeros(3)
#     base_orbit[axis_0] = n.sin(t*2*n.pi)
#     base_orbit[axis_1] = n.cos(t*2*n.pi)
#     base_orbit[free_axis] = 0
#     # base_orbit = n.array([n.sin(t*2*n.pi), 0, n.cos(t*2*n.pi)])

    

#     return rotate_vector(base_orbit, theta, phi)

# Because our coordinate system doesn't look so nice on vpython,
# we're gonna flip everything when passing to vpython
# this is kind of just asking for things to go wrong but its ok we'll figure it out
# flip of (1,2,0) makes x come out of the page, y to the right and z up when it is first loaded 
def vecflip(vin, flip=(1, 2, 0)):
    #print (vin[flip[0]], vin[flip[1]], vin[flip[2]])
    return vector(vin[flip[0]], vin[flip[1]], vin[flip[2]])
