import pykle_serial.pykle_serial as kle_serial
import math
from solid import *
from solid.utils import *

U = 19.05
KEYCAP_LEN = 18

def key_plate_footprint(key):
	w = U*key.width
	h = U*key.height
	model = key_plate_footprint_model()
	model = translate([w/2, h/2, 0])(model)
	model = key_place(key, model)
	return model

def key_plate_footprint_model():
	model = cube([14, 14, 10])
	model = translate([-7, -7, 0])(model)
	return model

def key_rotation(key, input, from_origin=True):
	if from_origin:
		rx = (key.rotation_x - key.x) * U
		ry = (key.rotation_y - key.y) * U
	else:
		rx = (key.rotation_x) * U
		ry = (key.rotation_y) * U

	return translate([rx, ry, 0])( rotate([0, 0, key.rotation_angle])( 
		translate([-rx, -ry, 0])(input)))

def key_place(key, model, from_origin=True):
	model = key_rotation(key, model, from_origin=from_origin)
	return translate([U*key.x, U*key.y, 0])(model)

def key_model(key):
	w = U*key.width
	h = U*key.height
	model = cube([w, h, 0.1])
	return key_place(key, model)
	

def keycap_model(key):
	keycap_margin = U - KEYCAP_LEN
	keycap_offset = keycap_margin / 2

	w = U*key.width - keycap_margin
	h = U*key.height - keycap_margin
	model = cube([w, h, 0.1])
	model = translate([keycap_offset, keycap_offset, 0 ])(model)

	model =  key_place(key, model)
	return model

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
