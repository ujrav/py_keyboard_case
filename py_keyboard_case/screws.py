from solid import *
from solid.utils import *


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

		screw_solid = shaft + head
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
		solid = cylinder(r=self.diameter_top/2, h=self.height, segments=100) + hole()(cylinder(r=self.diameter_bottom/2, h=self.height, segments=100))
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
	def __init__(self, screw_positions, screw_lengths, screw_diameters):
		self.screw_positions = screw_positions
		self.screw_lengths = screw_lengths
		self.screw_diameters = screw_diameters
