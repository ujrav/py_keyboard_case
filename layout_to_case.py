from argparse import ArgumentParser
import sys
import re
import json
import os
from turtle import position
from xxlimited import foo
import pykle_serial as kle_serial
import math
import numpy as np
import pdb
from solid import *
from solid.utils import *

from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import MultiPoint
from shapely.ops import unary_union

from py_keyboard_case.utils import *
from py_keyboard_case.screws import M2Screw, M2Standoff
from py_keyboard_case.port import Port, MicroUsbBreakout
from py_keyboard_case.tilt import Num10ScrewTilt

parser = ArgumentParser()
parser.add_argument('layout', type=str)
parser.add_argument('output', type=str)
parser.add_argument('--no_tilt', action="store_true")
parser.add_argument('--slice_plate_top', action="store_true")
args = parser.parse_args()

def main():
	print("loading json file:{}".format(args.layout))
	jsonFile  = open(args.layout,"r") if args.layout else sys.stdin
	layout = jsonFile.read()
	keyboard = kle_serial.parse(layout)

	key_solids = union()
	keycap_solids = union()
	key_footprints = union()

	rotated_key = [key for key in keyboard.keys if key.rotation_angle != 0]

	for key in keyboard.keys:
		key_box = key_solid(key)
		keycap = keycap_solid(key)
		footprint = key_plate_footprint(key, footprint_fn=key_plate_footprint_dual_acrylic_solid)

		key_solids += key_box
		keycap_solids += keycap
		key_footprints += footprint


	keys_filtered = [key for key in keyboard.keys if key.x < 10]
	keys_extent_verts = redox_tight_square_elec_compartment_polygon(keys_filtered)

	mid_screw_point = gen_key_midpoint_screw_point_location(
		[key for key in keys_filtered if key.rotation_angle == 0])

	if args.no_tilt:
		tilt_params = []
	else:
		tilt_params = [
			# (tilt class, face num, placement, place_mode, height, normal),
			(Num10ScrewTilt, 2, 12.989292131042735, "dist", 3*3.175, 1),
			(Num10ScrewTilt, 2, -12.989292131042735, "dist", 3*3.175, 1),
			(Num10ScrewTilt, 5, 12.989292131042735, "dist", 3*3.175, 1),
			(Num10ScrewTilt, 6, -12.989292131042735, "dist", 3*3.175, 1),
		]

	housing = Housing(keys_extent_verts, key_footprints, cavity_depth=4*3.175, plate_thickness=4.7625, port=BertoDoxPort(), aux_screw_points = [mid_screw_point], tilt_params=tilt_params)
	plate, case = housing.get_solid()

	output_dir = os.path.join("output", args.output)
	os.makedirs(output_dir, exist_ok=True)

	case_solid_for_slicing = housing.get_case_solid(mode="laser", align="bottom")
	layer_thicknesses = [3.175]*math.ceil(housing.case.height/3.175)
	if args.no_tilt:
		case_name = "case_no_tilt"
	else:
		case_name = "case"
	slice_write_solid(case_solid_for_slicing, output_dir, case_name, layer_thicknesses, x_tile=300, y_tile=200, aspect_ratio=0.66)

	plate_solid_for_slicing = housing.get_plate_solid(mode="laser")
	layer_thicknesses = [3.175, 1.5875]
	if args.slice_plate_top:
		plate_name = "plate_top"
		slice_mode = "top"
	else:
		plate_name = "plate"
		slice_mode = "bottom"
	slice_write_solid(plate_solid_for_slicing, output_dir, plate_name, layer_thicknesses, slice_mode=slice_mode)

	write_solid(os.path.join(output_dir, f"{case_name}.scad"), case)
	write_solid(os.path.join(output_dir, "plate.scad"), plate)

	write_solid(os.path.join(output_dir, "blown_up.scad"), housing.get_blown_up_solid())

	write_solid(os.path.join(output_dir, "screw_test.scad"), housing.get_screw_solids(mode='laser'))

	write_solid(os.path.join(output_dir, "port_negative.scad"), housing.port.get_solid())

	write_solid(os.path.join(output_dir, "key_plate_footprints.scad"), key_footprints)




def gen_key_midpoint_screw_point_location(keys):
	xs = np.array([key.x + key.width/2 for key in keys]) * U
	ys = np.array([key.y + key.height/2 for key in keys]) * U

	mid_x = 0.5*(np.max(xs) + np.min(xs))
	mid_y = 0.5*(np.max(ys) + np.min(ys))

	mid_key_idx = np.argmin((xs - mid_x)**2 + (ys - mid_y)**2)

	mid_key_adjacent_approx = (xs[mid_key_idx], ys[mid_key_idx] - U)

	mid_key_adjacent_idx = np.argmin((xs - mid_key_adjacent_approx[0])**2 + (ys - mid_key_adjacent_approx[1])**2)

	screw_point = (0.5*(xs[mid_key_idx] + xs[mid_key_adjacent_idx]),
		0.5*(ys[mid_key_idx] + ys[mid_key_adjacent_idx]))

	return screw_point


def write_solid(filename, solid):
	scad_str = scad_render(solid)

	with open(filename, 'w') as f:
		f.write(scad_str)

def slice_write_solid(solid, output_dir, name, layer_thicknesses,**kwargs):
	sliced_solid = slice_solid(solid, layer_thicknesses, **kwargs)

	write_solid(os.path.join(output_dir, f"sliced_{name}.scad"), sliced_solid)
	write_solid(os.path.join(output_dir, f"sliced_{name}_projection.scad"), projection(cut=True)(sliced_solid))

def redox_tight_square_polygon(keys):
	keys_square = [key for key in keys if key.rotation_angle == 0]
	keys_thumb_cluster = [key for key in keys if key.rotation_angle == 30]
	keys_ctrl = [key for key in keys if key.rotation_angle != 30 and key.rotation_angle != 0]

	keys_square_corners = key_list_corners(keys_square)
	keys_thumb_cluster_corners = key_list_corners(keys_thumb_cluster)
	keys_ctrl_corners = key_list_corners(keys_ctrl)

	keys_sqaure_poly_verts = min_bounding_box(keys_square_corners)
	keys_thumb_cluster_poly_verts = convex_hull(keys_thumb_cluster_corners)

	min_x_idx = np.argmin(keys_thumb_cluster_poly_verts[:,0])
	max_y_idx = np.argmax(keys_thumb_cluster_poly_verts[:,1])
	thumb_cluster_extension_vec = keys_thumb_cluster_poly_verts[min_x_idx,:] - keys_thumb_cluster_poly_verts[max_y_idx,:]
	keys_thumb_cluster_poly_verts[1,:] = keys_thumb_cluster_poly_verts[min_x_idx,:] + thumb_cluster_extension_vec

	redox_polygon_verts = combine_polygon_verts(keys_sqaure_poly_verts, keys_thumb_cluster_poly_verts)
	return redox_polygon_verts*U

def redox_tight_square_elec_compartment_polygon(keys):
	keys_square = [key for key in keys if key.rotation_angle == 0]
	keys_thumb_cluster = [key for key in keys if key.rotation_angle == 30]
	keys_ctrl = [key for key in keys if key.rotation_angle != 30 and key.rotation_angle != 0]

	keys_square_corners = key_list_corners(keys_square)
	keys_thumb_cluster_corners = key_list_corners(keys_thumb_cluster)
	keys_ctrl_corners = key_list_corners(keys_ctrl)

	keys_sqaure_poly_verts = min_bounding_box(keys_square_corners)
	keys_thumb_cluster_poly_verts = convex_hull(keys_thumb_cluster_corners)

	keys_thumb_cluster_poly_verts = keys_thumb_cluster_poly_verts[ 
		[ 	np.argmin(keys_thumb_cluster_poly_verts[:,0]),
			np.argmin(keys_thumb_cluster_poly_verts[:,1]),
			np.argmax(keys_thumb_cluster_poly_verts[:,0]),
			np.argmax(keys_thumb_cluster_poly_verts[:,1]),
		], :]

	min_x_idx = np.argmin(keys_thumb_cluster_poly_verts[:,0])
	max_y_idx = np.argmax(keys_thumb_cluster_poly_verts[:,1])
	thumb_cluster_extension_vec = keys_thumb_cluster_poly_verts[min_x_idx,:] - keys_thumb_cluster_poly_verts[max_y_idx,:]
	keys_thumb_cluster_poly_verts[min_x_idx,:] = keys_thumb_cluster_poly_verts[min_x_idx,:] + thumb_cluster_extension_vec

	redox_polygon_verts = combine_polygon_verts(keys_sqaure_poly_verts, keys_thumb_cluster_poly_verts)

	# remove point above thumbcluster to make electrical comparment
	redox_polygon_verts = redox_polygon_verts[redox_polygon_verts[:,1] != sorted(redox_polygon_verts[:,1])[3],:]

	# extend elec compartment top to the max x
	top_row_y = np.min(redox_polygon_verts[:,1])
	top_row_max_x = np.max(redox_polygon_verts[redox_polygon_verts[:,1] ==  top_row_y, :])
	max_x = np.max(redox_polygon_verts[:,0])

	top_row_left_corner_idx = np.logical_and(redox_polygon_verts[:, 0] == top_row_max_x, redox_polygon_verts[:,1] == top_row_y)
	redox_polygon_verts[top_row_left_corner_idx, 0] = max_x
	
	return redox_polygon_verts*U
	

class Housing:
	def __init__(
		self,
		key_extent_verts,
		key_footprints,
		plate_thickness=1.5,
		cavity_depth=9.525,
		cavity_border=-1.5,
		wall_thickness=8,
		port: Port=None,
		aux_screw_points=[],
		tilt_params=None):

		self.key_footprints = key_footprints
		self.plate_thickness = plate_thickness
		self.cavity_depth = cavity_depth
		self.cavity_border = cavity_border
		self.wall_thickness = wall_thickness

		key_outline_polygon = ShapelyPolygon(key_extent_verts)
		self.cavity_polygon = key_outline_polygon.buffer(self.cavity_border, cap_style=3, join_style=2)
		self.midline_polygon = self.cavity_polygon.buffer(self.wall_thickness/2, cap_style=3, join_style=2)
		outer_partial_polygon = self.midline_polygon.buffer(self.wall_thickness/4, cap_style=3, join_style=2)
		self.outer_polygon = outer_partial_polygon.buffer(self.wall_thickness/4, cap_style=3, join_style=1)

		self.outer_polygon_verts = get_shapely_exterior_array(self.outer_polygon)
		self.cavity_polygon_verts = get_shapely_exterior_array(self.cavity_polygon)

		self.screws = []
		screw_points = self.get_screw_points()

		# add aux screw points
		screw_points = np.concatenate((screw_points, np.array(aux_screw_points)), axis=0)

		self.port = port
		if port is not None:
			self.port.z = -self.cavity_depth
			self.port.place_on_case_polygon(self.outer_polygon_verts, place_offset=self.wall_thickness, placement='top_left')
			
			port_side_screw_points = self.port.get_side_screw_points(x_offset=self.wall_thickness/2, y_offset= -self.wall_thickness/2)
			screw_points = np.concatenate((screw_points, port_side_screw_points), axis=0)

		self.plate = Plate(self.outer_polygon_verts, self.key_footprints, height=self.plate_thickness)
		self.case = Case(self.outer_polygon_verts, self.cavity_polygon_verts, self.wall_thickness, self.cavity_depth, 3.175, port=self.port, tilt_params=tilt_params)

		self.place_screws(screw_points, placement="top")
		self.place_screws(screw_points, placement="bottom")
		self.place_standoffs(screw_points)

	def get_solid(self, mode='stl'):
		return self.get_plate_solid(mode=mode), self.get_case_solid(mode=mode)

	def get_blown_up_solid(self):
		plate = self.get_plate_solid()
		case = self.get_case_solid()

		case = down(10)(case)

		blown_up_solid = plate + case

		return blown_up_solid

	def get_screw_solids(self, mode='stl'):
		return union()(*[screw.get_solid(mode=mode) for screw in self.screws])

	def get_plate_solid(self, mode='stl'):
		return self.plate.get_solid(mode=mode) - self.get_screw_solids(mode=mode)

	def get_case_solid(self, mode = 'stl', align='top'):
		case_solid = self.case.get_solid(mode=mode) - self.get_screw_solids(mode=mode)

		if align == 'bottom':
			case_solid = up(self.case.height)(case_solid)
		
		return case_solid

	def get_screw_points(self):

		polygon_verts = np.stack(self.midline_polygon.exterior.xy, axis=1)
		return polygon_verts

	def place_screws(self, screw_points, length=6, screw_class=M2Screw, placement="top"):

		if placement == "top":
			z = self.plate.height
			rotation = [0,0,0]
			tolerance = 'low'
		elif  placement == "bottom":
			z = -1 * self.case.height
			rotation = [180, 0, 0]
			tolerance = 'high'
		else:
			raise ValueError("invalid screw placement")

		for screw_point in screw_points:
			screw = screw_class(length, position=[screw_point[0], screw_point[1], z], rotation=rotation, tolerance=tolerance)
			self.screws.append(screw)

	def place_standoffs(self, screw_points):
		length = self.case.cavity_depth
		for screw_point in screw_points:
			screw = M2Standoff(length, position=[screw_point[0], screw_point[1], 0])
			self.screws.append(screw) 


class Plate:
	def __init__(self, polygon_verts, key_footprints, height=1.5):
		self.polygon_verts = polygon_verts
		self.key_footprints = key_footprints
		self.height = height

	def get_solid(self, mode='stl'):
		plate = color([0,0,0])(
				linear_extrude(self.height, convexity=10)(
					polygon(array2tuples(self.polygon_verts))
				)
			)
		plate = plate - up(self.height)(self.key_footprints)
		return plate


class Case:
	def __init__(self, outer_polygon_verts, cavity_polygon_verts, wall_thickness, cavity_depth, bottom_thickness, port=None, tilt_params=None):
		self.outer_polygon_verts = outer_polygon_verts
		self.cavity_polygon_verts = cavity_polygon_verts
		self.wall_thickness = wall_thickness
		self.cavity_depth = cavity_depth
		self.bottom_thickness = bottom_thickness
		self.port = port

		self.height = self.cavity_depth + self.bottom_thickness

		self.tilt_mounts = []
		if tilt_params is not None:
			for tilt_class, face_num, placement, place_mode, tilt_height, norm in tilt_params:
				x, y, theta = place_along_face(cavity_polygon_verts, face_num, placement, mode=place_mode)
				theta = theta + 90 * (1 - norm)

				x = x - self.wall_thickness*np.sin(np.deg2rad(theta))
				y = y + self.wall_thickness*np.cos(np.deg2rad(theta))

				tilt_position = [x, y, -self.cavity_depth]
				tilt_rotation = [0, 0, theta]

				self.tilt_mounts.append(tilt_class(height=tilt_height, position=tilt_position, rotation=tilt_rotation))

	def get_solid(self, mode='stl'):
		case = color([0,1,0])(
					down(self.height)(linear_extrude(self.height, convexity=10)(
						polygon(array2tuples(self.outer_polygon_verts))
					)) - 
					down(self.cavity_depth)(linear_extrude(self.cavity_depth, convexity=10)(
						polygon(array2tuples(self.cavity_polygon_verts))
					)) -
					self.port.get_solid(mode=mode)
				)

		for tilt_mount in self.tilt_mounts:
			case += tilt_mount.get_solid(mode=mode)

		if mode=="stl":
			case += self.port.get_io_solid(mode=mode)

		return case

def slice_solid(solid, layer_thicknesses, x_tile=300, y_tile=300, aspect_ratio = 1.5, slice_mode="bottom", jitter_dist=0.01):
	assert slice_mode == "bottom" or slice_mode == "top", "slice mode must be either bottom or top"
	num_x = math.ceil(math.sqrt(len(layer_thicknesses) * aspect_ratio * y_tile / x_tile ))
	num_y = math.ceil(len(layer_thicknesses)/num_x)

	if slice_mode == "bottom":
		solid = down(jitter_dist)(solid)
	else:
		solid = up(jitter_dist)(solid)

	sliced_layers_solid = union()
	z = 0
	for i, layer_thickness in enumerate(layer_thicknesses):
		if slice_mode == "top":
			z += layer_thickness
		x_offset = x_tile*(i%num_x)
		y_offset = y_tile*math.floor(i/num_x)
		sliced_layer = slice_layer(solid, layer_thickness, z)
		sliced_layer = right(x_offset)(forward(y_offset)(sliced_layer))
		sliced_layers_solid += sliced_layer
		if slice_mode == "bottom":
			z += layer_thickness

	return sliced_layers_solid



def slice_layer(solid, layer_thickness, z):
	layer = up(z)(up(layer_thickness/2)(cube([2000, 2000, layer_thickness], center=True)))
	sliced_layer = down(z)(intersection()(solid, layer))
	return sliced_layer

class BertoDoxPort(Port):
	def __init__(self, *args, height=6.35, **kwargs):
		super().__init__(*args, height=height, **kwargs)

		left_micro_usb_x = -self.width/2 + MicroUsbBreakout.width/2 + 2
		right_micro_usb_x = left_micro_usb_x + MicroUsbBreakout.width + 2


		self.io_mods = [
			MicroUsbBreakout(left_micro_usb_x, 0, self.mount_thickness),
			MicroUsbBreakout(right_micro_usb_x, 0, self.mount_thickness),
			MicroUsbBreakout(left_micro_usb_x, -2*MicroUsbBreakout.length - 6, self.mount_thickness, theta=180),
		]

if __name__ == '__main__':
	main()
