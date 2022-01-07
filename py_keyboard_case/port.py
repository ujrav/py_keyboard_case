import math
import numpy as np

from solid import *
from solid.utils import *
from py_keyboard_case.utils import rotate_point
import py_keyboard_case.screws as screws

class Port:
    def __init__(self, width=40, length=20, height=3.175, theta=0, screw_left=False, screw_right=False):
        self.width = width
        self.length = length
        self.height = height
        self.theta = theta
        self.screw_left = screw_left
        self.screw_right = screw_right

        self.x = 0
        self.y = 0
        self.z = 0

    def get_solid(self, mode='stl'):
        cavity = cube([self.width, self.length, self.height])
        cavity = translate([-self.width/2, -self.length])(cavity)

        solid = cavity

        solid =  rotate([0, 0, self.theta])(solid)
        solid = translate([self.x, self.y, self.z])(solid)        

        return solid

    def get_side_screw_points(self, x_offset, y_offset):
        output = []

        screw_left_point = (self.x - self.width/2 - x_offset, self.y + y_offset)
        screw_right_point = (self.x + self.width/2 + x_offset, self.y + y_offset)
        if self.screw_left:
            rotated_screw_left_point = rotate_point(screw_left_point[0], screw_left_point[1], self.theta, x_offset=self.x, y_offset=self.y)
            output.append(list(rotated_screw_left_point))
        if self.screw_right:
            rotated_screw_right_point = rotate_point(screw_right_point[0], screw_right_point[1], self.theta, x_offset=self.x, y_offset=self.y)
            output.append(list(rotated_screw_right_point))

        return output

    def place_on_case_polygon(self, polygon_verts, place_offset, placement='top_left'):
        assert placement == 'top_left', "not placements besides 'top_left' are supported"

        min_y = np.min(polygon_verts[:, 1])
        max_x_at_min_y = np.max(polygon_verts[ polygon_verts[:,1] == min_y, 0])

        case_place_point = (max_x_at_min_y, min_y)

        port_place_point = (case_place_point[0] - (self.width/2 + place_offset), case_place_point[1])

        self.x = port_place_point[0]
        self.y = port_place_point[1]
        self.theta = 180
        self.screw_left = False
        self.screw_right = True


class MicroUsbBreakout:
    def __init__(self):
        self.height = 13.7
        self.width = 13.3

        screw_y = 7
        screw_x = 2.4, 10.9