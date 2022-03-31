import numpy as np
from math import cos, sin

def bezier(t, points):
    P1, P2, P3, P4 = points
    x = (1-t)**3*P1[0] + 3*(1-t)**2*t*P2[0] +3*(1-t)*t**2*P3[0] + t**3*P4[0]
    y = (1-t)**3*P1[1] + 3*(1-t)**2*t*P2[1] +3*(1-t)*t**2*P3[1] + t**3*P4[1]
    return x, y

def bezier_normal(t, points):
    P1, P2, P3, P4 = points
    dx = -3*(1-t)**2*P1[0] - 6*(1-t)*t*P2[0] +3*(1-t)**2*P2[0] - 3*t**2*P3[0] + 6 * (1-t)*t*P3[0] + 3*t**2*P4[0]
    dy = -3*(1-t)**2*P1[1] - 6*(1-t)*t*P2[1] +3*(1-t)**2*P2[1] - 3*t**2*P3[1] + 6 * (1-t)*t*P3[1] + 3*t**2*P4[1]
    theta = np.deg2rad(90)
    rot = np.array([[cos(theta), -sin(theta)], [sin(theta), cos(theta)]])
    normal = np.dot(rot, np.array([dx,dy]))
    return normal[0], normal[1]

def line(t, P0, P1):
    """ we construct the line, starting at P0 and ending at P1 """
    x = P0[0]*(1-t) + P1[0]*t
    y = P0[1]*(1-t) + P1[1]*t
    return x, y

def plane(s,t, orient):
    sp, p1, end, p2 = orient
    point = (1-t)*np.array(line(s, sp, p1)) + t*np.array(line(s, p2, end))
    return point[0], point[1]
