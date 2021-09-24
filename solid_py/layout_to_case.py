from argparse import ArgumentParser
import sys
import re
import json
import pykle_serial.pykle_serial as kle_serial
import solid
from solid import union, difference, translate, rotate, cube

parser = ArgumentParser()
parser.add_argument('layout', type=str)
parser.add_argument('output', type=str)
args = parser.parse_args()

print("loading json file:{}".format(args.layout))
jsonFile  = open(args.layout,"r") if args.layout else sys.stdin
layout = jsonFile.read()
keyboard = kle_serial.parse(layout)

# import pdb; pdb.set_trace()

key_models = union()

for key in keyboard.keys:
	 key_box = translate([key.rotation_x, key.rotation_y, 0])( rotate([0, 0, key.rotation_angle])( translate([-key.rotation_x, -key.rotation_y, 0])(
	 	translate([key.x, key.y, 0])(cube([0.9*key.width, 0.9*key.height, 0.1]))
 	)))

	 key_models += key_box

scad_str = solid.scad_render(key_models)

with open(args.output, 'w') as f:
	f.write(scad_str)