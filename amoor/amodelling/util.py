from math import sin, cos, radians


def rotate(x, y, deg):
    '''
    Rotate the cartesian coordinates, x and y, by deg degrees.
    Returns tuple with rotated x and y coordinates.
    '''
    x_rot = x * cos(radians(deg)) + y * sin(radians(deg))
    y_rot = y * cos(radians(deg)) - x * sin(radians(deg))
    return x_rot, y_rot


def cartesian(L, deg, displaced_x, displaced_y):
    '''
    Transform polar coordinates, length L and degree deg, to cartesian
    coordinates, then diplaces coordinates by displaced_x and displaced_y.
    Returns tuple with cartesian x and y values.
    '''
    x = displaced_x + L * sin(radians(deg))
    y = displaced_y + L * cos(radians(deg))
    return x, y