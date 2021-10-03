from argparse import ArgumentParser
import sys
import re
import json
import pykle_serial.pykle_serial as kle_serial
import math
import numpy as np
from solid import *
from solid.utils import *
from utils import *
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import MultiPoint
from shapely.ops import unary_union

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

	plate, case = build_housing(keys_extent_verts, key_footprints)

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

def build_housing(
	key_extent_verts,
	key_footprints,
	plate_thickness=1.5,
	cavity_depth=20,
	cavity_border=0,
	wall_thickness=7,
	):
	
	key_outline_polygon = ShapelyPolygon(key_extent_verts)
	cavity_polygon = key_outline_polygon.buffer(cavity_border, cap_style=3)
	outer_polygon = cavity_polygon.buffer(wall_thickness, cap_style=3)

	outer_polygon_verts = get_shapely_exterior_array(outer_polygon)
	cavity_polygon_verts = get_shapely_exterior_array(cavity_polygon)

	plate = build_plate(outer_polygon_verts, key_footprints, plate_thickness=plate_thickness)
	case = build_case(outer_polygon_verts, cavity_polygon_verts, cavity_depth, 3)

	return plate, case
	

def build_case(outer_polygon_verts, cavity_polygon_verts, cavity_depth, bottom_thickness):
	case_height = cavity_depth + bottom_thickness
	case = color([0,1,0])(
				down(case_height)(linear_extrude(case_height, convexity=10)(
					polygon(array2tuples(outer_polygon_verts))
				)) - 
				down(cavity_depth)(linear_extrude(cavity_depth, convexity=10)(
					polygon(array2tuples(cavity_polygon_verts))
				))
			)
	return case


def build_plate(plate_polygon_verts, key_footprints, plate_thickness=1.5):
	plate = color([0,0,0])(
				linear_extrude(plate_thickness, convexity=10)(
					polygon(array2tuples(plate_polygon_verts))
				)
			)
	plate = plate - key_footprints
	return plate



if __name__ == '__main__':
	main()
