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

	def get_solid(self):
		shaft = down(self.length)(cylinder(h=self.length, r=self.diameter/2, segments=100))
		head = self.head.get_solid()

		screw_solid = shaft + head
		screw_solid = translate(self._position)(rotate(self._rotation)(screw_solid))

		return screw_solid

class ScrewHead:
	def get_solid(self):
		return union()()

class FlatHead(ScrewHead):
	def __init__(self, diameter_top, diameter_bottom, height):
		self.diameter_top = diameter_top
		self.diameter_bottom = diameter_bottom
		self.height = height

	def get_solid(self):
		return down(self.height)(cylinder(r2=self.diameter_top/2, r1=self.diameter_bottom/2, h=self.height, segments=100))


class M2Screw(Screw):
	def __init__(self, length, head_type="flat"):
		if head_type == "flat":
			head = M2FlatHead()
		else:
			raise ValueError("Unsupported Head Type")

		super().__init__(diameter=2, length=length, head=head)

class M2FlatHead(FlatHead):
	def __init__(self):
		super().__init__(diameter_top=3.5, diameter_bottom=2, height=1.2)

