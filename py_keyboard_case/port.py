import math
from threading import local
from turtle import position
import numpy as np

from solid import *
from solid.utils import *
from py_keyboard_case.utils import rotate_point
from py_keyboard_case.screws import ZiptiePairM2

class Port:
    def __init__(self, width=40, length=20, height=3.175, theta=0, mount_thickness=3.175, screw_left=False, screw_right=False):
        self.width = width
        self.length = length
        self.height = height
        self.theta = theta
        self.screw_left = screw_left
        self.screw_right = screw_right
        self.mount_thickness = mount_thickness

        self.x = 0
        self.y = 0
        self.z = 0

        self.io_mods = []

    def get_solid(self, mode='stl'):
        cavity = cube([self.width, self.length, self.height])
        cavity = translate([-self.width/2, -self.length])(cavity)

        solid = cavity

        for io_mod in self.io_mods:
            solid += io_mod.get_mount_solid(mode=mode)  

        solid =  rotate([0, 0, self.theta])(solid)
        solid = translate([self.x, self.y, self.z])(solid)

        return solid

    def get_io_solid(self, mode='stl'):
        solid = union()
        for io_mod in self.io_mods:
            solid += io_mod.get_solid(mode=mode)
        
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
    length = 14.8
    width = 13.3
    height = 1.5
    def __init__(self, x, y, mount_thickness, theta=0,):
        
        self.x = x
        self.y = y
        self.theta = theta

        screw_y = - 7.8

        self.screws = [
            ZiptiePairM2(pair_dist=8.4, length=mount_thickness + self.height + .1, position=[0, screw_y, -mount_thickness], rotation=[180, 0, 0])
        ]

    def get_solid(self, mode='stl'):
        solid = cube([self.width, self.length, self.height])
        solid = translate([-self.width/2, -self.length, 0])(solid)

        screw_solid = self.get_screw_solids(mode=mode, local_ref=True)

        solid = solid - hole()(screw_solid)

        solid = translate([self.x, self.y, 0])(rotate([0, 0, self.theta])(solid))

        return solid
    
    def get_screw_solids(self, mode='stl', local_ref=False):
        screw_solid = union()
        for screw_obj in self.screws:
            screw_solid += screw_obj.get_solid(mode=mode)

        if not local_ref:
            screw_solid = translate([self.x, self.y, 0])(rotate([0, 0, self.theta])(screw_solid))
        return screw_solid

    def get_mount_solid(self, mode='stl'):
        return self.get_screw_solids(mode=mode)