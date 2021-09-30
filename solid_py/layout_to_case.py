from argparse import ArgumentParser
import sys
import re
import json
import pykle_serial.pykle_serial as kle_serial
import math
from solid import *
from solid.utils import *


U = 19.05
KEYCAP_LEN = 18

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


	keycap_models = color([1, 0, 0])(translate([0, 0, 0.1])(keycap_models))
	key_footprints = color([0, 0, 0])(translate([0, 0, -10])(key_footprints))

	plate = down(10)(down(5)(cube([200, 150, 1.5])) - key_footprints)

	scad_models = key_models + keycap_models + key_footprints + plate

	scad_str = scad_render(scad_models)

	with open(args.output, 'w') as f:
		f.write(scad_str)

def redox_tight_square_polygon(keys):
	keys_filtered = [key for key in keys if key.x < 200]

	keys_square = [key for key in keys_filtered if key.rotation_angle == 0]
	keys_thumb_cluster = [key for key in keys_filtered if key.rotation_angle == 30]

	keys_square_corners = np.array([])
	for k in keys_square:
		corners = np.array(key_corners(k))
		keys_square_corners.append(keys_square_corners, corners, axis=0)

if __name__ == '__main__':
	main()
