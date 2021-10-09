from argparse import ArgumentParser
import sys
import re
import json
import pykle_serial as kle_serial
import math
import numpy as np
from solid import *
from solid.utils import *

from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import MultiPoint
from shapely.ops import unary_union

from py_keyboard_case.utils import *
from py_keyboard_case.screws import M2Screw

parser = ArgumentParser()
parser.add_argument('layout', type=str)
parser.add_argument('output', type=str)
args = parser.parse_args()

def main():
	print("loading json file:{}".format(args.layout))
	jsonFile  = open(args.layout,"r") if args.layout else sys.stdin
	layout = jsonFile.read()
	keyboard = kle_serial.parse(layout)

	key_models = union()
	keycap_models = union()
	key_footprints = union()

	rotated_key = [key for key in keyboard.keys if key.rotation_angle != 0]

	for key in keyboard.keys:
		 key_box = key_model(key)
		 keycap = keycap_model(key)
		 footprint = key_plate_footprint(key)

		 key_models += key_box
		 keycap_models += keycap
		 key_footprints += footprint


	keys_extent_verts = redox_tight_square_polygon(keyboard.keys)

	housing = Housing(keys_extent_verts, key_footprints)
	plate, case = housing.get_solid()

	keycap_models = color([1, 0, 0])(translate([0, 0, 0.1])(keycap_models))
	key_footprints = color([0, 0, 0])(translate([0, 0, -10])(key_footprints))
	plate = down(5)(plate)
	case = down(10)(case)

	scad_models = key_models + keycap_models + plate + case

	scad_str = scad_render(scad_models)

	with open(args.output, 'w') as f:
		f.write(scad_str)

def redox_tight_square_polygon(keys):
	keys_filtered = [key for key in keys if key.x < 10]

	keys_square = [key for key in keys_filtered if key.rotation_angle == 0]
	keys_thumb_cluster = [key for key in keys_filtered if key.rotation_angle == 30]
	keys_ctrl = [key for key in keys_filtered if key.rotation_angle != 30 and key.rotation_angle != 0]

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
	

class Housing:
	def __init__(
		self,
		key_extent_verts,
		key_footprints,
		plate_thickness=1.5,
		cavity_depth=12,
		cavity_border=-2,
		wall_thickness=5,):

		self.key_footprints = key_footprints
		self.plate_thickness = plate_thickness
		self.cavity_depth = cavity_depth
		self.cavity_border = cavity_border
		self.wall_thickness = wall_thickness

		key_outline_polygon = ShapelyPolygon(key_extent_verts)
		self.cavity_polygon = key_outline_polygon.buffer(self.cavity_border, cap_style=3, join_style=2)
		self.outer_polygon = self.cavity_polygon.buffer(self.wall_thickness, cap_style=3, join_style=2)

		self.outer_polygon_verts = get_shapely_exterior_array(self.outer_polygon)
		self.cavity_polygon_verts = get_shapely_exterior_array(self.cavity_polygon)

		self.plate = Plate(self.outer_polygon_verts, self.key_footprints, height=self.plate_thickness)
		self.case = Case(self.outer_polygon_verts, self.cavity_polygon_verts, self.cavity_depth, 3)

		self.screws = []
		screw_points = self.get_screw_points()
		self.place_screws(screw_points, placement="top")
		self.place_screws(screw_points, placement="bottom")

	def get_solid(self):
		screw_solids = union()(*[screw.get_solid() for screw in self.screws])

		plate_solid = self.plate.get_solid() - screw_solids + color([1,0,0])(up(100)(screw_solids))
		case_solid = self.case.get_solid() - screw_solids

		return plate_solid, case_solid

	def get_screw_points(self):
		screw_line_polygon = self.cavity_polygon.buffer(self.wall_thickness/2, cap_style=3, join_style=2)

		polygon_verts = np.stack(screw_line_polygon.exterior.xy, axis=1)
		return polygon_verts

	def place_screws(self, screw_points, length=6, screw_class=M2Screw, placement="top"):

		if placement == "top":
			z = self.plate.height
			rotation = [0,0,0]
		elif  placement == "bottom":
			z = -1 * self.case.height
			rotation = [180, 0, 0]
		else:
			raise ValueError("invalid screw placement")

		for screw_point in screw_points:
			screw = screw_class(length)
			screw.position = [screw_point[0], screw_point[1], z]
			screw.rotation = rotation

			self.screws.append(screw)


class Plate:
	def __init__(self, polygon_verts, key_footprints, height=1.5):
		self.polygon_verts = polygon_verts
		self.key_footprints = key_footprints
		self.height = height

	def get_solid(self):
		plate = color([0,0,0])(
				linear_extrude(self.height, convexity=10)(
					polygon(array2tuples(self.polygon_verts))
				)
			)
		plate = plate - self.key_footprints
		return plate


class Case:
	def __init__(self, outer_polygon_verts, cavity_polygon_verts, cavity_depth, bottom_thickness):
		self.outer_polygon_verts = outer_polygon_verts
		self.cavity_polygon_verts = cavity_polygon_verts
		self.cavity_depth = cavity_depth
		self.bottom_thickness = bottom_thickness

		self.height = self.cavity_depth + self.bottom_thickness

	def get_solid(self):
		case = color([0,1,0])(
					down(self.height)(linear_extrude(self.height, convexity=10)(
						polygon(array2tuples(self.outer_polygon_verts))
					)) - 
					down(self.cavity_depth)(linear_extrude(self.cavity_depth, convexity=10)(
						polygon(array2tuples(self.cavity_polygon_verts))
					))
				)
		return case


if __name__ == '__main__':
	main()
