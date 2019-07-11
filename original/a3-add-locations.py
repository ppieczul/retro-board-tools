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

# This script reads component locations from a CSV file in format:
# <ID>;<X>;<Y>;<W>;<H>
# and adds a JSON element called "box" with these parameters to the wire list JSON.
#
# Author: Pawel Pieczul
#

import sys, re, json
from json import JSONDecodeError
from json import JSONEncoder

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
	return data

def check_integer(i, idx):
	if i is None or not re.match("[-\d]+", i):
		print("Wrong value {} not integer in line {}".format(i, idx))
		sys.exit()

def process_csv(csv, json):
	for idx,line in enumerate(csv):
		x = re.split(";", line.rstrip().lstrip())
		if (len(x) < 5 or any([i == "" for i in x])):
			print("Error: incomplete line {}".format(idx))
			sys.exit()
		c = json["components"][x[0].upper()]
		if c is None or c == "":
			print("Unknown component {} in line {}".format(x[0], idx))
		check_integer(x[1], idx)
		check_integer(x[2], idx)
		check_integer(x[3], idx)
		check_integer(x[4], idx)
		c["box"] = [int(x[1]), int(x[2]), int(x[3]), int(x[4])]

class ObjectEncoder(JSONEncoder):
	def default(self, o):
		return o.__dict__    

def main(argv):
	if len(argv) < 3:
		print("\nUsage:", argv[0], "<locations-file.csv> <json-file.json>\n")
		return -1
	j = load_json(argv[2])

	try:
		file = open(argv[1], "r")
	except IOError:
		print("\nCan't open file:", fname, "\n")
		return -1
	process_csv(file, j)
	file.close()
	print(json.dumps(j, sort_keys=True, indent=4, cls=ObjectEncoder))


if __name__ == "__main__":
	assert sys.version_info >= (3, 0)
	main(sys.argv[0:])
