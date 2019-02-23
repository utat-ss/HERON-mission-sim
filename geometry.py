import numpy as n

from vpython import vector


def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / n.linalg.norm(vector)


def dot_and_angle(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::

            >>> angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            >>> angle_between((1, 0, 0), (1, 0, 0))
            0.0
            >>> angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    dot = n.clip(n.dot(v1_u, v2_u), -1.0, 1.0)
    return dot, n.arccos(dot)

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

# dont be fooled
# these are not standard euler angles
# psi is applied first, it is the rotation in the y-axis
# theta is next, it is the rotation around the x-axis
# phi is last, it is the rotation around the z-axis
# the rotations are always around the original coordinate frame, not rotated coordinate frames
def rotate_vector(v, theta = 0, phi = 0, psi=0):
    v = n.array(v).reshape(3)
    rot_matrix_d = n.array([[n.cos(phi), n.sin(phi), 0],
                            [-n.sin(phi), n.cos(phi), 0],
                            [0, 0, 1]])

    rot_matrix_c = n.array([[1, 0, 0],
                            [0, n.cos(theta), n.sin(theta)],
                            [0, -n.sin(theta), n.cos(theta)]])

    rot_matrix_b = n.array([[n.cos(psi), 0, -n.sin(psi)],\
                            [0, 1, 0],\
                            [n.sin(psi), 0, n.cos(psi)]])
 
    rot_matrix_cb = n.matmul(rot_matrix_c, rot_matrix_b)
    rot_matrix_dcb = n.matmul(rot_matrix_d, rot_matrix_cb)
    # print (rot_matrix_cb)
#     rot_matrix = n.matmul(rot_matrix_b, rot_matrix_cd)

    return n.matmul(rot_matrix_dcb, v.T)


def orbit_xyz(t,  # time elapsed / period, 0 < t < 1
              theta=0,
              phi=0,
              starting_position = (0,0,1)
              ):

    starting_position = n.array(starting_position)
    return rotate_vector(starting_position, theta, phi, 2*n.pi*t)


# Because our coordinate system doesn't look so nice on vpython,
# we're gonna flip everything when passing to vpython
# this is kind of just asking for things to go wrong but its ok we'll figure it out
# flip of (1,2,0) makes x come out of the page, y to the right and z up when it is first loaded 
def vecflip(vin, flip=(1, 2, 0), signs = (1,1,1)):
    #print (vin[flip[0]], vin[flip[1]], vin[flip[2]])
    return vector(signs[0] * vin[flip[0]], signs[1] * vin[flip[1]], signs[2] * vin[flip[2]])
