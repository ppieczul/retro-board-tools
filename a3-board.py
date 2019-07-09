#!/opt/local/bin/python3.7

# Apple /// Board Schematic Tools
# Copyright (C) 2019 oldcrap.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# This program loads Apple /// wire list from a JSON file and displays information
# about components and traces of the board. Various ways of filtering and presenting
# the data are available.
#
# Author: Pawel Pieczul
#

import sys, re, json, getopt, fnmatch
from json import JSONDecodeError
from collections import namedtuple

global prog_name

class MotherBoard:
	def __init__(self, json):
		if "components" not in json or "traces" not in json:
			print("Json does not contain components/traces on top level.")
			return
		self.components = json["components"]
		self.traces = json["traces"]

def is_id_power(id):
	return id in ("GND", "+12V", "-12V", "+5V", "-5V", "+12FV", "-12FV", "+5FV", "-5FV", "GNDF")

def load_json(fname):
	try:
		file = open(fname, "r")
	except IOError:
		print("\nCan't open file:", fname, "\n")
		return
	try:
		data = json.load(file)
	except JSONDecodeError as e:
		print("\nError decoding JSON file: {}\n".format(e))
		return
	finally:
		file.close()
	return MotherBoard(data)

def format_pins(pins, level):
	txt = ""
	if level in [0, 1]:
		idx = 1
		for trace in pins:
			if txt != "":
				txt += " "
			txt += str(idx) + "="
			if trace == "":
				txt += "-"
			else:
				txt += trace
			idx += 1
	return txt

def format_component(component, level, id_width, single_mode):
	if level == 0:
		if single_mode:
			return "{} ({}): {}".format(component["id"], component["part"], format_pins(component["pins"], level))
		else:
			return "{} ({})".format(component["id"], component["part"])
	elif level == 1:
		return  "{}: {}{}, {}, {}".format( \
				component["id"].rjust(id_width), 
				component["part"],
				"" if component["type"] == "" else "/" + component["type"],
				component["location"],
				format_pins(component["pins"], level))

def format_trace(id, trace, level, id_width):
	if level == 0:
		return id
	elif level == 1:
		if is_id_power(id):
			return "{}: ...".format(id.rjust(id_width))
		else:
			txt = ""
			for t in trace:
				pin = "{}-{}".format(t[0], t[1] + 1)
				txt += "{:<8}".format(pin)
			return "{}: {}".format(id.rjust(id_width), txt)

def usage():
	print()
	print("USAGE:", prog_name, "[options]")
	print()
	print("OPTIONS:")
	print("  {:<33} {}".format("-c,--component <id1>[,<id2>,...]", "Display given component IDs (wildcards allowed for each ID)"))
	print("  {:<33} {}".format("-h,--help", "Display help"))
	print("  {:<33} {}".format("-j,--json <json>", "Use a given JSON file with wire list"))
	print("  {:<33} {}".format("-l,--level <level>", "Set output detail level (0 or 1)"))
	print()
	print("EXAMPLES:")
	print("  {} -c* -l1".format(prog_name))
	print("      Display all components and all traces in medium details level.")
	print()
	print("  {} -cC*".format(prog_name))
	print("      Display all capacitors in a short way.")
	print()
	print("  {} -cU160,R5,X* -l1".format(prog_name))
	print("      Display chip U160, resistor R5 and all diodes in medium details level.")
	print()
	sys.exit()

def print_in_line(fmt, start):
	print(("{}" if start else ", {}").format(fmt), end="")

def main(argv):
	try:
		opts, args = getopt.getopt(argv, "hj:c:l:",["help","json=","component=","level="])
	except getopt.GetoptError:
		usage()

	if len(opts) == 0:
		usage()

	json_file = "./original/a3-wire-list.json"
	component_filter = "*"
	output_level = 0

	for opt, arg in opts:
		if opt in ["-h", "--help"]:
			usage()
		elif opt in ["-c", "--component"]:
			component_filter = arg.upper()
		elif opt in ["-j", "--json"]:
			json_file = arg
		elif opt in ["-l", "--level"]:
			output_level = int(arg)

	board = load_json(json_file)
	if board is None:
		return

	print()
	filters = re.split(",", component_filter)
	components = [board.components[key] for key in board.components.keys() \
					if any([fnmatch.fnmatch(key, filter) for filter in filters])]
	traces = {key : board.traces[key] for key in board.traces.keys() \
				if any([any([fnmatch.fnmatch(v, filter) for v in [t[0] for t in board.traces[key]]]) for filter in filters])}
	if len(components) == 0:
		return

	tid_width = max([len(key) for key in traces.keys()])
	cid_width = max([len(c["id"]) for c in components])
	id_width = max([tid_width, cid_width])

	start = True
	single_mode = (len(components) == 1)
	for c in components:
		fmt = format_component(c, output_level, id_width, single_mode)
		if output_level == 0:
			print_in_line(fmt, start)
		elif output_level == 1:
			print(fmt)
		start = False
	if output_level == 0 and not single_mode:
		print()
	print()

	if output_level > 0 or not single_mode:
		start = True
		for k, v in traces.items():
			fmt = format_trace(k, v, output_level, id_width)
			if output_level == 0:
				print_in_line(fmt, start)
			elif output_level == 1:
				print(fmt)
			start = False
		if output_level == 0:
			print()
	print()

if __name__ == "__main__":
	assert sys.version_info >= (3, 0)
	prog_name = sys.argv[0]
	main(sys.argv[1:])
