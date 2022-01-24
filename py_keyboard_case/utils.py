from abc import ABC, abstractmethod
import math
import numpy as np
from solid import *
from solid.utils import *
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import MultiPoint
from shapely.ops import unary_union


U = 19.05
KEYCAP_LEN = 18

class Obj3D(ABC):
	def __init__(self, position: list = None, rotation: list = None):
		if position is None:
			position = [0, 0, 0]
		if rotation is None:
			rotation = [0, 0, 0]

		assert isinstance(position, list) and len(position) == 3, "position must be list of len 3"
		assert isinstance(rotation, list) and len(rotation) == 3, "rotation must be list of len 3"

		self.position = position.copy()
		self.rotation = rotation.copy()

	def get_solid(self, mode='stl'):
		solid = self._get_solid(mode)
		solid = self._translate_solid(solid)
		return solid

	def _translate_solid(self, solid):
		solid = rotate(self.rotation)(solid)
		solid = translate(self.position)(solid)
		return solid

	@abstractmethod
	def _get_solid(self, mode):
		raise NotImplementedError


def key_plate_footpint_endmill_corners_solid(endmill_diameter=3.4):
	r = endmill_diameter / 2
	x_offset = 7 - r*math.sin(math.pi/4)
	y_offset = x_offset
	h = 5

	footprint_solid = key_plate_footprint_solid()

	for x_sign in [-1, 1]:
		x = x_sign * x_offset
		for y_sign in [-1, 1]:
			y = y_sign * y_offset

			cyl_solid = cylinder(h=h, r=r, segments=100)
			cyl_solid = translate([x,y,-h])(cyl_solid)

			footprint_solid += cyl_solid

	return footprint_solid

def key_plate_footprint_solid(h = 5):
	solid = cube([14, 14, h])
	solid = translate([-7, -7, 0])(solid)
	solid = down(h)(solid)
	return solid

def key_plate_footprint_dual_acrylic_solid(h=5, top_plate_height=1.5875):
	solid = key_plate_footprint_solid(h=h)

	sp_len = 15.5
	support_plate_footprint = cube([14, sp_len, h])
	support_plate_footprint = translate([-7, -sp_len/2, -top_plate_height-h])(support_plate_footprint)

	solid = solid + support_plate_footprint

	return solid

def key_plate_footprint(key, footprint_fn=key_plate_footprint_solid):
	w = U*key.width
	h = U*key.height
	solid = footprint_fn()
	solid = translate([w/2, h/2, 0])(solid)
	solid = key_place(key, solid)
	return solid

def key_rotation(key, input, from_origin=True):
	if from_origin:
		rx = (key.rotation_x - key.x) * U
		ry = (key.rotation_y - key.y) * U
	else:
		rx = (key.rotation_x) * U
		ry = (key.rotation_y) * U

	return translate([rx, ry, 0])( rotate([0, 0, key.rotation_angle])(
		translate([-rx, -ry, 0])(input)))

def key_place(key, solid, from_origin=True):
	solid = key_rotation(key, solid, from_origin=from_origin)
	return translate([U*key.x, U*key.y, 0])(solid)

def key_solid(key):
	w = U*key.width
	h = U*key.height
	solid = cube([w, h, 0.1])
	return key_place(key, solid)
	

def keycap_solid(key):
	keycap_margin = U - KEYCAP_LEN
	keycap_offset = keycap_margin / 2

	w = U*key.width - keycap_margin
	h = U*key.height - keycap_margin
	solid = cube([w, h, 0.1])
	solid = translate([keycap_offset, keycap_offset, 0 ])(solid)

	solid =  key_place(key, solid)
	return solid

def compute_key_corners(key):
	bottom_left = (key.x, key.y)
	bottom_right = (key.x + key.width, key.y)
	top_right = (key.x + key.width, key.y + key.height)
	top_left = (key.x, key.y + key.height)

	bottom_left = key_rotation_apply(key, *bottom_left)
	bottom_right = key_rotation_apply(key, *bottom_right)
	top_right = key_rotation_apply(key, *top_right)
	top_left = key_rotation_apply(key, *top_left)

	return bottom_left, bottom_right, top_right, top_left

def key_rotation_apply(key, x_in, y_in):
	rot_rad = key.rotation_angle * math.pi/180

	offset_x = key.rotation_x
	offset_y = key.rotation_y

	offset_x = x_in - key.rotation_x
	offset_y = y_in - key.rotation_y

	x = offset_x * math.cos(rot_rad) - offset_y * math.sin(rot_rad)
	y = offset_x * math.sin(rot_rad) + offset_y * math.cos(rot_rad)

	x = x + key.rotation_x
	y = y + key.rotation_y

	return x,y

def rotate_point(x, y, theta, x_offset=0, y_offset=0, degrees=True):
	x = x - x_offset
	y = y - y_offset

	if degrees:
		theta = math.radians(theta)

	x_rot = x * math.cos(theta) - y * math.sin(theta)
	y_rot = x * math.sin(theta) + y * math.cos(theta)

	x_rot += x_offset
	y_rot += y_offset

	return x_rot, y_rot

def min_bounding_box(vertices):
	max_x = np.max(vertices[:,0])
	min_x = np.min(vertices[:,0])
	max_y = np.max(vertices[:,1])
	min_y = np.min(vertices[:,1])

	return np.array([
		[max_x, max_y],
		[max_x, min_y],
		[min_x, min_y],
		[min_x, max_y],
	])

def convex_hull(vertices):
	hull = MultiPoint(vertices).convex_hull
	return get_shapely_exterior_array(hull)

def key_list_corners(keys):
	key_corners = np.empty((0, 2))
	for k in keys:
		corners = np.array(compute_key_corners(k))
		key_corners = np.append(key_corners, corners, axis=0)
	return key_corners

def combine_polygon_verts(*args):
	polygons = [ShapelyPolygon(verts) for verts in args]
	combined_polygon = unary_union(polygons)
	return get_shapely_exterior_array(combined_polygon)

def get_shapely_exterior_array(polygon):
	return np.stack(polygon.exterior.xy, axis=1)

def array2tuples(verts):
	tuples = []
	for row in verts:
		tuples.append((row[0], row[1]))

	return tuples

def place_along_face(verts, face_num, placement, mode='dist'):
	face_a = verts[face_num-1,:]
	face_b = verts[face_num, :]

	face_len = np.linalg.norm(face_b - face_a)
	face_vec = face_b - face_a

	if placement >= 0:
		place_start = face_a
	else:
		place_start = face_b

	if mode == 'dist':
		position = place_start + face_vec * placement / face_len
	elif mode == 'ratio':
		position = place_start + face_vec*placement
	
	theta = np.rad2deg(np.arctan2(face_vec[1], face_vec[0]))

	return position[0], position[1], theta

