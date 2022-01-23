from turtle import position
from matplotlib.pyplot import axis
from solid import *
from solid.utils import *
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import LineString
from py_keyboard_case.utils import *


class Screw:
	def __init__(self, diameter, length, head=None):
		self.diameter = diameter
		self.length = length
		self.head = head if head is not None else ScrewHead()

		self._position = [0, 0, 0]
		self._rotation = [0, 0, 0]

	@property
	def position(self):
		return self._position
	

	@position.setter
	def position(self, value):
		self._position = value.copy()

	@property
	def rotation(self):
		return self._rotation
	

	@rotation.setter
	def rotation(self, value):
		self._rotation = value.copy()

	def get_solid(self, mode='stl'):
		if isinstance(self.diameter, dict):
			diameter = self.diameter[mode]
		else:
			diameter = self.diameter
		shaft = down(self.length)(cylinder(h=self.length, r=diameter/2, segments=100))
		head = self.head.get_solid(mode=mode)

		screw_solid = part()(shaft + head)
		screw_solid = translate(self._position)(rotate(self._rotation)(screw_solid))

		return screw_solid


class ScrewHead:
	def get_solid(self, mode='stl'):
		return union()()


class ScrewHeadMulti:
	def __init__(self, head_map):
		self.head_map = head_map

	def get_solid(self, mode='stl'):
		return self.head_map.get(mode, ScrewHead()).get_solid(mode=mode)


class FlatHead(ScrewHead):
	def __init__(self, diameter_top, diameter_bottom, height):
		self.diameter_top = diameter_top
		self.diameter_bottom = diameter_bottom
		self.height = height

	def get_solid(self, mode=None):
		solid = cylinder(r2=self.diameter_top/2, r1=self.diameter_bottom/2, h=self.height, segments=100)
		return down(self.height)(solid)

class FlatHeadLaser(FlatHead):
	def get_solid(self, mode=None):
		solid = cylinder(r=self.diameter_top/2, h=self.height, segments=100) - hole()(cylinder(r=self.diameter_bottom/2, h=self.height, segments=100))
		return down(self.height)(solid)

class M2Screw(Screw):
	def __init__(self, length, head_type="flat"):
		if head_type == "flat":
			head = M2FlatHead()
		else:
			raise ValueError("Unsupported Head Type")

		super().__init__(diameter={'stl': 2, 'laser': 1.9, 'cnc':2}, length=length, head=head)

class M2FlatHead(ScrewHeadMulti):
	def __init__(self):

		super().__init__({
			'stl': FlatHead(diameter_top=3.5, diameter_bottom=2, height=1.2),
			'laser': FlatHeadLaser(diameter_top=4.4, diameter_bottom=1.9, height=1.2),
			'cnc': ScrewHead(),
		})

class M2Standoff(Screw):
	def __init__(self, length=8):
		super().__init__(diameter=3, length=length)


class ZiptiePair:
	def __init__(self, pair_dist, length, head_length, hole_diameter, head_diameter, position: list = None, rotation: list = None):

		if position is None:
			position = [0, 0, 0]
		if rotation is None:
			rotation = [0, 0, 0]

		assert isinstance(position, list) and len(position) == 3, "position must be list of len 3"
		assert isinstance(rotation, list) and len(rotation) == 3, "rotation must be list of len 3"

		self.pair_dist = pair_dist
		self.length = length
		self.head_length = head_length
		self.hole_diameter = hole_diameter
		self.head_diameter = head_diameter
		self.position = position.copy()
		self.rotation = rotation.copy()

	def get_solid(self, mode="stl"):

		hole_solids = left(self.pair_dist/2)(cylinder(r=self.hole_diameter/2, h=self.length, segments=100)) + \
					  right(self.pair_dist/2)(cylinder(r=self.hole_diameter/2, h=self.length, segments=100))

		head_line = LineString([(-self.pair_dist/2, 0, 0), (self.pair_dist/2, 0, 0)])
		head_verts = head_line.buffer(self.head_diameter/2).exterior.xy
		head_solid = linear_extrude(self.head_length, convexity=10)(
					polygon(array2tuples(np.stack((head_verts[0], head_verts[1]), axis=1)))
				)

		pair_solid = hole_solids + head_solid

		if mode == "laser":
			pair_solid -= intersection()(hole_solids, head_solid)

		pair_solid = rotate([180, 0, 0])(pair_solid)

		pair_solid = rotate(self.rotation)(pair_solid)
		pair_solid = translate(self.position)(pair_solid)

		return pair_solid

class ZiptiePairM2(ZiptiePair):
	def __init__(self, pair_dist, length, position=None, rotation=None):
		super().__init__(pair_dist, length, head_length=1.2, hole_diameter=2, head_diameter=3.4, position=position, rotation=rotation)
