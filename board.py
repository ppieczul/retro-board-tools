#!/opt/local/bin/python3.7

# Retro Board Schematic Tools
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
# This program loads a wire list from a JSON file and displays information
# about components and traces of the board. Various ways of filtering and presenting
# the data are available.
#
# Author: Pawel Pieczul
#

import sys, re, json, getopt, fnmatch, matplotlib, numpy, math
from json import JSONDecodeError
from matplotlib import image
from matplotlib import pyplot
from matplotlib.patches import Rectangle, PathPatch, Polygon, Circle
from matplotlib.text import TextPath
from matplotlib.transforms import Affine2D
from functools import reduce

global prog_name

class MotherBoard:
	def __init__(self, json):
		if "components" not in json or "traces" not in json:
			print("Json does not contain components/traces on top level.")
			return
		self.components = json["components"]
		self.traces = json["traces"]
		if "board_image" in json:
			self.board_image = json["board_image"]
		else:
			self.board_image = None

def usage():
	print()
	print("USAGE:", prog_name, " -c<ids>|-t<ids> [options] <board-file.json>")
	print()
	print("OPTIONS:")
	print("  {:<33} {}".format("-c,--component <id1>[,<id2>,...]", "Display components (wildcards allowed for each ID)"))
	print("  {:<33} {}".format("-g,--graphics", "Display board image with annotations"))
	print("  {:<33} {}".format("-h,--help", "Display help"))
	print("  {:<33} {}".format("-s,--sequential", "Display traces for each component separately"))
	print("  {:<33} {}".format("-t,--trace <id1>[,<id2>,...]", "Display traces (wildcards allowed for each ID)"))
	print()
	print("EXAMPLES:")
	print("  {} -c* -s a3-board.json".format(prog_name))
	print("      Display all components and all traces one by one.")
	print()
	print("  {} -cC* c64-board.json".format(prog_name))
	print("      Display all capacitors and a combined trace.")
	print()
	print("  {} -cU160,R5,X*  a3-board.json".format(prog_name))
	print("      Display chip U160, resistor R5 and all diodes and a combined trace.")
	print()
	sys.exit()

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

def format_component(id, c, id_width, part_width, single_mode, sequential_filter):
	return "{}: {} {}{}".format( \
		id.rjust(id_width),  \
		(c["part"] + ("" if c["type"] == "" else "/" + c["type"])).ljust(part_width), \
		c["location"].ljust(3), "" if single_mode or sequential_filter else format_pins(c["pins"]))

def format_trace(id, trace, id_width, single_mode):
	if is_id_power(id):
		return "{}: ...".format(id.rjust(id_width))
	else:
		trace.sort(key = lambda x: x[0][0] + x[0][1:].zfill(3) + str(x[1]).zfill(2))
		txt = ""
		for t in trace:
			pin = "{}-{}".format(t[0], t[1] + 1)
			txt += ("{} " if single_mode else "{:<8}").format(pin)
		return "{}: {}".format(id.rjust(id_width), txt)

def draw_text(txt, x, y, w, h, gca):
	rotate = (w < h)
	tp = TextPath((0, 0), txt, size = (w if rotate else h) * 0.7)
	tbox = tp.get_extents()
	if not rotate:
		xtr = x + (w - tbox.width) / 2
		ytr = y - h + (h - tbox.height) / 2
		tp = tp.transformed(Affine2D().translate(xtr, ytr))
	else:
		xtr = x + tbox.height + (w - tbox.height) / 2
		ytr = y - h + (h - tbox.width) / 2
		tp = tp.transformed(Affine2D().rotate_deg(90) + Affine2D().translate(xtr, ytr))
	txt = PathPatch(tp, linewidth=0.5, facecolor = "0", edgecolor = "0")
	gca.add_patch(txt)

def draw_component(id, c, gca):
	if gca is not None and "box" in c:
		colors = { "U" : "#00ff00", \
				   "L" : "#ff0000", \
				   "J" : "#ffff00", \
				   "Q" : "#ff0000", \
				   "P" : "#ff00ff"}
		b = c["box"]; t = id[0]
		x = b[0]; y = 2000 - b[1]; w = b[2]; h = b[3]
		color = colors[t] if t in colors else "#000000"
		rect = Rectangle((x, y), w, h, linewidth = 1.5, edgecolor = color, facecolor = color + "60", zorder = 1)
		gca.add_patch(rect)
		draw_text(id, x, y, abs(w), abs(h), gca)

def print_components(board, component_filter, sequential_filter, gca):
	print()
	filters = re.split(",", component_filter)
	components = [board.components[key] for key in board.components.keys() \
					if any([fnmatch.fnmatch(key, filter) for filter in filters])]
	if len(components) == 0:
		return
	components.sort(key = lambda x: x["id"][0] + x["id"][1:].zfill(4))

	traces = {key : board.traces[key] for key in board.traces.keys() \
				if any([any([fnmatch.fnmatch(v, filter) for v in [t[0] for t in board.traces[key]]]) \
						for filter in filters])}

	tid_width = max([len(key) for key in traces.keys()])
	cid_width = max([len(c["id"]) for c in components])
	id_width = max([tid_width, cid_width])
	part_width = max([len(c["part"]) + len(c["type"]) + 1 for c in components])
	single_mode = (len(components) == 1)

	for c in components:
		id = c["id"]
		print(format_component(id, c, cid_width, part_width, single_mode, sequential_filter))
		if sequential_filter or single_mode:
			print()
			for pin, t in enumerate(c["pins"]):
				fmt = "-".rjust(id_width) if t == "" else format_trace(t, traces[t], id_width, single_mode)
				print("{:>2}: {}".format(pin + 1, fmt))
			print()
		draw_component(id, c, gca)

	if not single_mode and not sequential_filter: 
		print()
		for k, v in traces.items():
			print(format_trace(k, v, id_width, single_mode))
		print()

def print_traces(board, trace_filter, sequential_filter, gca):
	print()
	filters = re.split(",", trace_filter)
	traces = {key : board.traces[key] for key in board.traces.keys() \
			if any([fnmatch.fnmatch(key, filter) for filter in filters])}
	if len(traces) == 0:
		return

	single_mode = (len(traces) == 1)
	tid_width = max([len(key) for key in traces.keys()])

	for key, tr in sorted(traces.items()):
		tr.sort(key = lambda x: x[0] + str(x[1]).zfill(3))
		print(format_trace(key, tr, tid_width, single_mode))

		cs = [board.components[i[0]] for i in tr]
		pins = [i[1] for i in tr]
		cid_width = max([len(c["id"]) for c in cs])
		part_width = max([len(c["part"]) + len(c["type"]) + 1 for c in cs])

		if sequential_filter or single_mode:
			print()
			for idx, c in enumerate(cs):
				id = c["id"]
				print(format_component(id, c, cid_width, part_width, single_mode, sequential_filter))
				draw_component(id + "-" + str(pins[idx] + 1), c, gca)
			
			if gca is not None:
				p = [(c["box"][0] + c["box"][2] / 2, 2000 - c["box"][1] + c["box"][3] / 2) for c in cs if "box" in c]
				center = reduce(lambda a, b: (a[0] + b[0], a[1] + b[1]), p, (0, 0))
				center = (center[0] / len(p), (center[1] / len(p)))
				p.sort(key = lambda a: math.atan2(a[1] - center[1], a[0] - center[0]))
				poly = Polygon(p, closed = True, fill = False, linewidth = 2, edgecolor = "#ffffff", zorder = 0.5)
				gca.add_patch(poly)
	print()

def main(argv):
	try:
		opts, args = getopt.getopt(argv, "ghc:t:s",["graphics", "help","component=","trace=", "sequential"])
	except getopt.GetoptError:
		usage()

	if len(opts) == 0 or len(args) < 1:
		usage()

	json_file = args[0]
	board = load_json(json_file)
	if board is None: 
		return

	component_filter = None
	trace_filter = None
	sequential_filter = False
	gca = None

	for opt, arg in opts:
		if opt in ["-h", "--help"]:
			usage()
		elif opt in ["-c", "--component"]:
			component_filter = arg.upper()
		elif opt in ["-t", "--trace"]:
			trace_filter = arg.upper()
		elif opt in ["-s", "--sequential"]:
			sequential_filter = True
		elif opt in ["-g", "--graphics"] and board.board_image is not None:
			matplotlib.rcParams['figure.figsize'] = (14.0, 9.0)
			data = image.imread("./pictures/" + board.board_image)
			data = numpy.flipud(data)
			pyplot.axis("off")
			pyplot.imshow(data, origin = "lower")
			gca = pyplot.gca()

	if component_filter is None and trace_filter is None:
		usage()

	if component_filter is not None and trace_filter is not None:
		print("Define only one: -c or -t")
		return

	if component_filter is not None:
		print_components(board, component_filter, sequential_filter, gca)
	elif trace_filter is not None:
		print_traces(board, trace_filter, sequential_filter, gca)

	if gca is not None:
		pyplot.show()

if __name__ == "__main__":
	assert sys.version_info >= (3, 0)
	prog_name = sys.argv[0]
	main(sys.argv[1:])
