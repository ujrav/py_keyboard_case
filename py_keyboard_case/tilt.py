from os import major
from solid import *
from solid.utils import *
from copy import deepcopy

import numpy as np

from py_keyboard_case.utils import Obj3D

class HexNut(Obj3D):
    def __init__(self, height, major_diameter=None, minor_diameter=None, **kwargs):
        super().__init__(**kwargs)
        assert (major_diameter is None) != (minor_diameter is None), "define one of major_diameter or minor_diameter only"
        assert (major_diameter is not None) or (minor_diameter is not None), "define one of major_diameter or minor_diameter only"

        if minor_diameter is not None:
            major_diameter = minor_diameter / np.cos(np.deg2rad(30))
        else:
            minor_diameter = major_diameter * np.cos(np.deg2rad(30))

        self.major_diameter = major_diameter
        self.minor_diameter = minor_diameter

        self.height = height

    def _get_solid(self, mode):
        solid = cylinder(r=self.major_diameter/2, h=self.height, segments=6)

        return solid


class Num10HexNut(HexNut):
    def __init__(self, height=3.175, **kwargs):
        super().__init__(height=height, minor_diameter=9.4, **kwargs)


class ScrewTilt(Obj3D):
    def __init__(self, hex_nut: HexNut, shaft_diameter, height, buffer_width=3, slope=1.732, **kwargs):
        super().__init__(**kwargs)
        self.shaft_diameter = shaft_diameter
        self.height = height
        self.buffer_width = buffer_width
        self.slope = slope

        self.buffer_diameter = hex_nut.major_diameter + 2*self.buffer_width
        self.buffer_radius = self.buffer_diameter/2

        self.hex_nuts = [deepcopy(hex_nut), deepcopy(hex_nut)]
        self.hex_nuts[0].position = [0, self.buffer_radius, 0]
        self.hex_nuts[1].position = [0, self.buffer_radius, self.height - hex_nut.height]

    def _get_solid(self, mode):
        
        self.buffer_radius = self.buffer_diameter/2
        solid = forward(self.buffer_radius)(cylinder(r=self.buffer_radius, h=self.height, segments=100))

        trap = self._get_trap(self.buffer_radius)

        solid += trap

        for nut in self.hex_nuts:
            solid -= nut.get_solid(mode=mode)

        solid -= forward(self.buffer_radius)(down(1)(cylinder(r=self.shaft_diameter/2, h=self.height+2, segments=100)))

        return solid



    def _get_trap(self, r):
        slope_theta = np.arctan(self.slope)

        trap_y = r * (1 + np.cos(slope_theta))
        trap_x_top = r*np.sin(slope_theta)
        trap_x_bottom = trap_y / self.slope + trap_x_top

        trap_verts = [
            (trap_x_bottom, -.1),
            (trap_x_bottom, 0),
            (trap_x_top, trap_y),
            (-trap_x_top, trap_y),
            (-trap_x_bottom, 0),
            (-trap_x_bottom, -.1),
        ]

        trap = linear_extrude(self.height, convexity=10)(
            polygon(trap_verts)
        )

        return trap

class Num10ScrewTilt(ScrewTilt):
    def __init__(self, height, **kwargs):
        super().__init__(Num10HexNut(), 4.8, height, **kwargs)

