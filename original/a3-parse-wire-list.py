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

# This script parses the original Apple /// board wire list contained in the
# Apple /// Service Reference Manual, Section II or II, Servicing Information, 
# Chapter 15, Wire List.
# It returns a JSON with all components and all traces on the board.
# It validates the contents against naming conventions, completeness of component
# description data and overlapping between traces.
#
# Author: Pawel Pieczul
#

import sys, re, json
from json import JSONEncoder

class ObjectEncoder(JSONEncoder):
	def default(self, o):
		return o.__dict__    

class MotherBoard:
	traces = {}
	components = {}
	noname_trace_idx = 1
	board = {"components" : components, "traces" : traces}
	def toJson(self):
		return json.dumps(self.board, sort_keys=True, indent=4, cls=ObjectEncoder)

class Component:
	def __init__(self, board, id, pages, part, pin_count, type="", location=""):
		traces = board.traces
		components = board.components
		if len(type) > 0 and len(location) == 0:
			location = type
			type = ""
		if not re.match("[A-Z]+[0-9]+", id):
			raise ValueError("Wrong component ID syntax ({})".format(id))
		self.id = id
		if not re.match("(\d\-?)+", pages):
			raise ValueError("Wrong schematic pages syntax ({})".format(pages))
		self.pages = [int(i) + 1 for i in re.split("-", pages)]
		if not re.match("[\.\w]+", part):
			raise ValueError("Wrong component value syntax ({})".format(value))
		self.part = part
		if not re.match("\d+", pin_count):
			raise ValueError("Wrong component pin count syntax ({})".format(pin_count))
		self.pin_count = int(pin_count)
		if self.pin_count < 1 or self.pin_count > 50:
			raise ValueError("Wrong number of pins ({})".format(pin_count))	 
		if len(type) > 0 and not re.match("\w+", type):
			raise ValueError("Wrong component type syntax ({})".format(type))
		self.type = type
		if len(location) > 0 and not re.match("[A-Z]+\d+", location):
			raise ValueError("Wrong board location syntax ({})".format(location))
		self.location = location
		self.pins = {}
		board.components[self.id] = self

	def add_trace(self, board, pin, name, trace=[]):
		traces = board.traces
		components = board.components
		if pin < 1 or pin > self.pin_count:
			raise ValueError("Pin ({}) out of component range ({})".format(pin, comp.pin_count))
		if len(trace) == 0:
			if name not in ("NOCONNECTION", "GND", "+12V", "-12V", "+5V", 
		 					"-5V", "+12FV", "-12FV", "+5FV", "-5FV", "GNDF"):
				print("trace:{}".format(name))
				raise ValueError("Wrong trace name for short pin ({})".format(name))
			if name == "NOCONNECTION":
				name = ""
				if len(trace) > 0:
					raise ValueError("Trace exist for no connection pin")
		elif not re.match("^[\?\w\/\*\&]+", name):
			raise ValueError("Wrong trace name ({})".format(name))
		for connection in trace:
			if not re.match("[A-Z]+[0-9]+", connection):
				raise ValueError("Wrong connection in trace ({})".format(connection))
		if len(set(trace)) != len(trace):
			raise ValueError("Trace contains duplicate values")		
		cnt = 0
		for tr in traces.keys():
			cnt = 0
			for cn in trace:
				if cn in traces[tr]:
					cnt += 1
			if cnt > 0:
				if cnt != len(trace):
					raise ValueError("Trace ({}:{}) different to already stored ({}:{})".format(name, trace, tr, traces[tr]))		
				if name == "?":
					name = tr;
				elif name != tr:
					raise ValueError("Trace ({}) named differently than already stored ({})".format(name, tr))		
				elif self.id + "-" + str(pin) not in traces[tr]:
					raise ValueError("Source pin ({}) name not part of the trace list".format(pin))		
				break
		if cnt == 0:
			if name == "?":
				name = "T" + str(board.noname_trace_idx).zfill(3);
				board.noname_trace_idx += 1
			if name != "" and len(trace) == 0:
				if name in traces.keys():
					a = traces[name]
				else:
					a = []
				traces[name] = a + [[self.id, str(pin - 1)]]
			else:
				if name != "":
					new_trace = []
					for t in trace:
						i = re.split("-", t)
						new_trace.append([i[0], int(i[1]) - 1])
					traces[name] = new_trace
		self.pins[pin] = name

	def validate(self):
		pins = self.pins
		self.pins = []
		test_pins = list(range(1, 1 + self.pin_count))
		for pin in pins.keys():
			if pin not in test_pins:
				raise ValueError("Pin ({}) failed validation".format(pin))
			test_pins.remove(pin)
		if len(test_pins) > 0:
			raise ValueError("Missing pins definition ({})".format(test_pins))
		for pin in list(range(1, 1 + self.pin_count)):
			self.pins.append(pins[pin])

def process_file(file, board):
	header = True
	line_number = 0
	expected_pin = 0
	for line in file:
		line_number += 1
		if not line.strip(): continue
		line = line.rstrip().lstrip()
		if re.match("^[A-Z].+", line):
			# validate previous component
			if 'comp' in locals():
				comp.validate()
			# header format is:
			# <component-id> <schematic-pages> <component-value> <number-of-pins> [component-type] [board-location]
			h = re.split("\s+", line)
			hl = len(h)
			expected_pin = 0
			try:
				if hl < 4:
					print(line_number, ": Component header too short ({})".format(hl))
				elif hl > 6:
					print(line_number, ": Component header too long ({})".format(hl))
				else:
					comp = Component(board, *h)
			except ValueError as e:
				print(line_number, ":", e)
		elif re.match("^[0-9]+\s+.+", line):
			# pin definition line, format is:
			# <pin-number> <trace-name> <component-id-1> [component-id-2] ...
			h = re.split("\s+", line)
			hl = len(h)
			expected_pin += 1
			if 'comp' not in locals():
				print(line_number, ": Unexpected pin - no component")
			elif hl < 2:
				print(line_number, ": Pin description too short ({})".format(hl))
			elif not re.match("\d+", h[0]):
				print(line_number, ": Wrong pin number syntax ({})".format(h[0]))
			else:
				pin = int(h[0])
				if pin != expected_pin:
					print(line_number, ": Pin ({}) but expected pin ({})".format(pin, expected_pin))
				else:
					try:							
						comp.add_trace(board, pin, h[1], h[2:])
					except ValueError as e:
						print(line_number, ":", e)
		else:
			print(line_number, ": Ambiguous line ({})".format(line))
			expected_pin = 0
	comp.validate()

def read_file(fname):
	try:
		file = open(fname, "r")
	except IOError:
		print("\nCan't open file:", fname, "\n")
		return -1
	board = MotherBoard()
	process_file(file, board)
	file.close()
	print(board.toJson())

def main(argv):
	if len(argv) < 2:
		print("\nUsage:", argv[0], "<netlist-file>\n")
		return -1
	return read_file(argv[1])

if __name__ == "__main__":
	assert sys.version_info >= (3, 0)
	main(sys.argv[0:])
