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

def format_pins(pins):
	txt = ""
	for idx, trace in enumerate(pins):
		txt += "" if txt == "" else " "
		txt += str(idx + 1) + "="
		txt += "-" if trace == "" else trace
	return " (" + txt + ")"

def format_trace(id, trace, id_width):
	if is_id_power(id):
		return "{}: ...".format(id.rjust(id_width))
	else:
		trace.sort(key = lambda x: x[0] + str(x[1]).zfill(2))
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
	print("  {:<33} {}".format("-s,--sequential", "Display traces for each component separately"))
	print()
	print("EXAMPLES:")
	print("  {} -c* -s".format(prog_name))
	print("      Display all components and all traces one by one.")
	print()
	print("  {} -cC*".format(prog_name))
	print("      Display all capacitors and a combined trace.")
	print()
	print("  {} -cU160,R5,X*".format(prog_name))
	print("      Display chip U160, resistor R5 and all diodes and a combined trace.")
	print()
	sys.exit()

def main(argv):
	try:
		opts, args = getopt.getopt(argv, "hj:c:s",["help","json=","component=","sequential"])
	except getopt.GetoptError:
		usage()

	if len(opts) == 0:
		usage()

	json_file = "./original/a3-wire-list.json"
	component_filter = "*"
	sequential_filter = False

	for opt, arg in opts:
		if opt in ["-h", "--help"]:
			usage()
		elif opt in ["-c", "--component"]:
			component_filter = arg.upper()
		elif opt in ["-j", "--json"]:
			json_file = arg
		elif opt in ["-s", "--sequential"]:
			sequential_filter = True

	board = load_json(json_file)
	if board is None: 
		return

	print()
	filters = re.split(",", component_filter)
	components = [board.components[key] for key in board.components.keys() \
					if any([fnmatch.fnmatch(key, filter) for filter in filters])]
	traces = {key : board.traces[key] for key in board.traces.keys() \
				if any([any([fnmatch.fnmatch(v, filter) for v in [t[0] for t in board.traces[key]]]) \
						for filter in filters])}

	if len(components) == 0:
		return

	tid_width = max([len(key) for key in traces.keys()])
	cid_width = max([len(c["id"]) for c in components])
	id_width = max([tid_width, cid_width])
	part_width = max([len(c["part"]) + len(c["type"]) + 1 for c in components])
	single_mode = (len(components) == 1)

	components.sort(key = lambda x: x["id"][0] + x["id"][1:].zfill(4))
	for c in components:
		print("{}: {} {}{}".format( \
			c["id"].rjust(cid_width),  \
			(c["part"] + ("" if c["type"] == "" else "/" + c["type"])).ljust(part_width), \
			c["location"].ljust(3), "" if single_mode else format_pins(c["pins"])))
		if sequential_filter or single_mode:
			print()
			for pin, t in enumerate(c["pins"]):
				fmt = "-".rjust(id_width) if t == "" else format_trace(t, traces[t], id_width)
				print("{:>2}: {}".format(pin + 1, fmt))
			print()

	if not single_mode and not sequential_filter: 
		print()
		for k, v in traces.items():
			print(format_trace(k, v, id_width))
		print()

if __name__ == "__main__":
	assert sys.version_info >= (3, 0)
	prog_name = sys.argv[0]
	main(sys.argv[1:])
