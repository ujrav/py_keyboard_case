import math
from solid import *
from solid.utils import *

U = 19.05
KEYCAP_LEN = 18

def key_plate_footprint(key):
	w = U*key.width
	h = U*key.height
	solid = key_plate_footpint_endmill_corners_solid()
	solid = translate([w/2, h/2, 0])(solid)
	solid = key_place(key, solid)
	solid = down(5)(solid)
	return solid

def key_plate_footpint_endmill_corners_solid(endmill_diameter=3.4):
	r = endmill_diameter / 2
	x_offset = 7 - r*math.sin(math.pi/4)
	y_offset = x_offset

	footprint_solid = key_plate_footprint_solid()

	for x_sign in [-1, 1]:
		x = x_sign * x_offset
		for y_sign in [-1, 1]:
			y = y_sign * y_offset

			cyl_solid = cylinder(h=10, r=r, segments=100)
			cyl_solid = translate([x,y,0])(cyl_solid)

			footprint_solid += cyl_solid

	return footprint_solid


def key_plate_footprint_solid():
	solid = cube([14, 14, 10])
	solid = translate([-7, -7, 0])(solid)
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