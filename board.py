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

import datetime
import fnmatch
import getopt
import math
import numpy
import json
from re import split
from json import load
from functools import reduce
from sys import exit, version_info, argv

from PIL import Image
from matplotlib import pyplot
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle, PathPatch, Polygon
from matplotlib.text import TextPath
from matplotlib.transforms import Affine2D


class MotherBoard:
    def __init__(self, json_dict, black_white):
        if "components" not in json_dict or "traces" not in json_dict:
            print("Json does not contain components/traces on top level.")
        else:
            self.components = json_dict["components"]
            self.traces = json_dict["traces"]
            if "board_image" in json_dict:
                img = Image.open("./pictures/" + json_dict["board_image"])
                if black_white:
                    img = img.convert("L")
                self.image = numpy.flipud(numpy.asarray(img))
            else:
                self.image = None


def usage():
    print()
    print("USAGE:", prog_name, " -c<ids>|-t<ids> [options] <board-file.json>")
    print()
    print("MANDATORY:")
    print("  {:<33} {}".format("-j,--json <json-file>", "Use JSON file with board definitions"))
    print()
    print("MANDATORY (ONE OF OPTIONS MUST BE PRESENT):")
    print(
        "  {:<33} {}".format("-c,--component <id1>[,<id2>,...]", "Display components (wildcards allowed for each ID)"))
    print("  {:<33} {}".format("-t,--trace <id1>[,<id2>,...]", "Display traces (wildcards allowed for each ID)"))
    print()
    print("OPTIONAL:")
    print("  {:<33} {}".format("   --colors", "Draw board image in colors (default is b & w)"))
    print("  {:<33} {}".format("-d,--detailed", "Display details about components or traces"))
    print("  {:<33} {}".format("-g,--graphics", "Draw board image on screen"))
    print("  {:<33} {}".format("-h,--help", "Display help"))
    print("  {:<33} {}".format("-m,--merge", "Merge and display/draw all concerning traces at once"))
    print("  {:<33} {}".format("-n,--neighbors", "Draw component neighbors too (valid with -c and -g)"))
    print()
    print("EXAMPLES:")
    print("  {} --json=a3-board.json -c* -d".format(prog_name))
    print("      Display all components and their pins/traces one by one.")
    print()
    print("  {} --json=c64-board.json -cC* -m".format(prog_name))
    print("      Display all capacitors and a combined trace.")
    print()
    print("  {} --json=a3-board.json -cU160,R5,X* -g -n".format(prog_name))
    print("      Display chip U160, resistor R5 and all diodes, draw them and their neighbors.")
    print()
    exit()


def is_id_power(cid):
    return cid in ("GND", "+12V", "-12V", "+5V", "-5V", "+12FV", "-12FV", "+5FV", "-5FV", "GNDF")


def load_json(fname, black_white):
    try:
        file = open(fname, "r")
    except IOError:
        print("\nCan't open file:", fname, "\n")
        return
    try:
        data = load(file)
    except json.JSONDecodeError as e:
        print("\nError decoding JSON file: {}\n".format(e))
        return
    finally:
        file.close()
    try:
        board = MotherBoard(data, black_white)
    except IOError:
        print("\nCan't open board image file.\n")
        return
    return board


def format_pins(pins):
    txt = ""
    for idx, trace in enumerate(pins):
        txt += "" if txt == "" else " "
        txt += str(idx + 1) + "="
        txt += "-" if trace == "" else trace
    return " (" + txt + ")"


def format_component(cid, c, id_width, part_width, adjust, show_pins):
    return "{}: {} {}{}".format(
        cid.rjust(id_width if adjust else 0),
        (c["part"] + ("" if c["type"] == "" else "/" + c["type"])).ljust(part_width if adjust else 0),
        c["location"].ljust(3 if adjust else 0),
        format_pins(c["pins"]) if show_pins else ""
    )


def format_trace(cid, trace, id_width, adjust):
    if is_id_power(cid):
        return "{}: ...".format(cid.rjust(id_width if adjust else 0))
    else:
        trace.sort(key=lambda x: x[0][0] + x[0][1:].zfill(3) + str(x[1]).zfill(2))
        txt = ""
        for t in trace:
            pin = "{}-{}".format(t[0], t[1] + 1)
            txt += ("{:<8}" if adjust else "{} ").format(pin)
        return "{}: {}".format(cid.rjust(id_width if adjust else 0), txt)


def draw_text(txt, x, y, w, h, gca):
    v_max_scale = 0.7
    h_max_scale = 0.8

    rotate = (abs(w) < abs(h))
    fp = FontProperties(family="arial")
    fsize = w if rotate else h
    tp = TextPath((0, 0), txt, size=fsize, prop=fp)

    bw, bh = w, h
    (__, __, tw, th) = tp.get_extents().bounds
    if rotate:
        tp = tp.transformed(Affine2D().rotate_deg(90).translate(th, 0))
        bw, bh = bh, bw

    if tw < h_max_scale * bw:
        scale = v_max_scale * bh / th
    else:
        scale = h_max_scale * bw / tw
    tp = tp.transformed(Affine2D().scale(scale))
    (__, __, tw, th) = tp.get_extents().bounds

    tp = tp.transformed(Affine2D().translate(x + (w - tw) / 2, y + (h - th) / 2))

    txt = PathPatch(tp, linewidth=0.3, facecolor="0", edgecolor="0")
    gca.add_patch(txt)


def draw_description(txt, gca):
    gca.text(0, 0, txt, size=15)


def draw_component(cid, c, gca, edge_color=None):
    if gca is not None and "box" in c:
        colors = {"U": "#00ff00",
                  "L": "#ff0000",
                  "J": "#ffff00",
                  "Q": "#ff0000",
                  "P": "#ff00ff",
                  "C": "#00ffff",
                  "R": "#ff3388",
                  "X": "#ff0000",
                  "Y": "#33ff88",
                  "T": "#9955ff"}
        b = c["box"]
        t = cid[0]
        x = b[0]
        y = b[1]
        w = b[2]
        h = b[3]
        color = colors[t] if t in colors else "#000000"
        rect = Rectangle((x, y), w, h, linewidth=1.5 if edge_color is None else 2,
                         edgecolor=color if edge_color is None else edge_color, facecolor=color + "40", zorder=1)
        gca[0].add_patch(rect)
        draw_text(cid, x, y, w, h, gca[0])


def draw_neighbors(board, cid, component, trace, gca):
    for t in board.traces[trace]:
        neighbor = board.components[t[0]]
        if neighbor["id"] != cid and "box" in neighbor and "box" in component:
            draw_component(neighbor["id"], neighbor, gca)
            p = [component_center(neighbor), component_center(component)]
            line = Polygon(p, closed=False, fill=False, linewidth=1, edgecolor="#ffffffff", zorder=0.5)
            gca[0].add_patch(line)


def display_figure(figure, display, pdf):
    if display:
        pyplot.show()
    if pdf is not None:
        pdf.savefig(figure, dpi=60, orientation="portrait", facecolor="#ffffffff")
    pyplot.close(figure)


def print_components(board, component_filter, detailed, merged, neighbors, display, pdf, gca):
    print()
    filters = split(",", component_filter)
    components = [board.components[key] for key in board.components.keys()
                  if any([fnmatch.fnmatch(key, flt) for flt in filters])]
    if len(components) == 0:
        return
    components.sort(key=lambda x: x["id"][0] + x["id"][1:].zfill(4))

    traces = {key: board.traces[key] for key in board.traces.keys()
              if any([any([fnmatch.fnmatch(v, flt)
                           for v in [t[0] for t in board.traces[key]]]) for flt in filters])}

    tid_width = max([len(key) for key in traces.keys()])
    cid_width = max([len(c["id"]) for c in components])
    id_width = max([tid_width, cid_width])
    part_width = max([len(c["part"]) + len(c["type"]) + 1 for c in components])

    for c in components:
        cid = c["id"]
        print(format_component(cid, c, cid_width, part_width, not detailed, not detailed))
        if detailed:
            print()
        for pin, t in enumerate(c["pins"]):
            if detailed:
                fmt = "-".rjust(id_width) if t == "" else format_trace(t, traces[t], id_width, True)
                print("{:>2}: {}".format(pin + 1, fmt))
            if neighbors and t != "" and not is_id_power(t) and gca is not None:
                draw_neighbors(board, cid, c, t, gca)
        if detailed:
            print()
        if gca is not None:
            draw_component(cid, c, gca, edge_color="#ff0000ff" if neighbors else None)
            if not merged:
                draw_description("Component: " + cid, gca[2])
                display_figure(gca[3], display, pdf)
                gca = init_gca(board)
    if not detailed:
        print()
    if merged:
        for k, v in traces.items():
            print(format_trace(k, v, id_width, True))
        print()
        if gca is not None:
            draw_description("Component: multiple", gca[2])
            display_figure(gca[3], display, pdf)


def component_center(c):
    b = c["box"]
    return b[0] + b[2] / 2, b[1] + b[3] / 2


def print_traces(board, trace_filter, detailed, merged, display, pdf, gca):
    print()
    filters = split(",", trace_filter)
    traces = {key: board.traces[key] for key in board.traces.keys()
              if any([fnmatch.fnmatch(key, flt) for flt in filters])}
    if len(traces) == 0:
        return

    tid_width = max([len(key) for key in traces.keys()])

    color = 0xff
    items = len(traces)
    sorted_traces = sorted(traces.items())
    for key, tr in sorted_traces:
        tr.sort(key=lambda x: x[0] + str(x[1]).zfill(3))
        print(format_trace(key, tr, tid_width, not detailed))

        cs = [(board.components[i[0]], i[1]) for i in tr]
        cid_width = max([len(c["id"]) + 3 for (c, __) in cs])
        part_width = max([len(c["part"]) + len(c["type"]) + 1 for (c, __) in cs])

        if detailed:
            print()
        for (c, pin) in cs:
            cid = c["id"]
            if detailed:
                print(format_component(cid + "-" + str(pin + 1), c, cid_width, part_width, True, False))
            draw_component(cid + ("-" + str(pin + 1) if not merged else ""), c, gca)

        if detailed:
            print()
        if gca is not None:
            p = [component_center(c) for (c, __) in cs if "box" in c]
            if len(p) > 0:
                center = reduce(lambda a, b: (a[0] + b[0], a[1] + b[1]), p, (0, 0))
                center = (center[0] / len(p), (center[1] / len(p)))
                p.sort(key=lambda a: math.atan2(a[1] - center[1], a[0] - center[0]))
                q = int(color)
                poly = Polygon(p, closed=True, fill=False, linewidth=2,
                               edgecolor="#{:02X}{:02X}{:02X}".format(q, q, q), zorder=0.5)
                gca[0].add_patch(poly)
            if not merged:
                draw_description("Trace: " + key, gca[2])
                display_figure(gca[3], display, pdf)
                gca = init_gca(board)
            else:
                draw_description("Traces: multiple", gca[2])
                color = color - (0xff / items)
    if not detailed:
        print()
    if merged:
        display_figure(gca[3], display, pdf)


def init_gca(board):
    fig = pyplot.figure(figsize=(14, 9))
    p0 = fig.add_subplot(3, 1, 1, position=[0, 0.95, 1, 0.05])
    p0.axis("off")
    p1 = fig.add_subplot(3, 1, 2, position=[0, 0.25, 1, 0.70])
    p1.axis("off")
    p1.imshow(board.image, origin="lower", interpolation="nearest", cmap=pyplot.get_cmap("Greys_r"))
    p2 = fig.add_subplot(3, 1, 3, position=[0, 0.00, 1, 0.25], xlim=(0, 40), ylim=(0, 7))
    p2.axis("off")
    return p1, p2, p0, fig


def main(main_argv):
    try:
        opts, args = getopt.getopt(
            main_argv, "ghc:t:dmnj:p:",
            ["graphics", "help", "component=", "trace=", "details", "merge", "neighbors", "json=", "pdf=", "colors"]
        )
    except getopt.GetoptError:
        usage()
        return

    if len(opts) == 0 or len(args) > 1:
        usage()

    pdf_file = None
    pdf = None
    json_file = None
    component_filter = None
    trace_filter = None
    neighbors = False
    detailed = False
    display = False
    merged = False
    gca = None
    black_white = True

    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            usage()
        elif opt in ["-j", "--json"]:
            json_file = arg
        elif opt in ["-p", "--pdf"]:
            pdf_file = arg
        elif opt in ["-c", "--component"]:
            component_filter = arg.upper()
        elif opt in ["-t", "--trace"]:
            trace_filter = arg.upper()
        elif opt in ["-d", "--details"]:
            detailed = True
        elif opt in ["-m", "--merge"]:
            merged = True
        elif opt in ["-n", "--neighbors"]:
            neighbors = True
        elif opt in ["-g", "--graphics"]:
            display = True
        elif opt in ["--colors"]:
            black_white = False

    if json_file is None:
        usage()

    board = load_json(json_file, black_white)
    if board is None:
        return

    if display or pdf_file is not None:
        gca = init_gca(board)

    if component_filter is None and trace_filter is None:
        usage()

    if component_filter is not None and trace_filter is not None:
        print("Define only one: -c or -t")
        return

    if pdf_file is not None:
        try:
            pdf = PdfPages(pdf_file)
        except IOError:
            usage()
        d = pdf.infodict()
        if component_filter is not None:
            d["Title"] = "Components of board " + json_file
        else:
            d["Title"] = "Traces of board " + json_file
        d["Author"] = "oldcrap.org"
        d["Subject"] = "Automatically generated file containing information about board components and traces"
        d["CreationDate"] = d["ModDate"] = datetime.datetime.today()

    if component_filter is not None:
        print_components(board, component_filter, detailed, merged, neighbors, display, pdf, gca)
    elif trace_filter is not None:
        print_traces(board, trace_filter, detailed, merged, display, pdf, gca)

    if pdf is not None:
        pdf.close()


if __name__ == "__main__":
    assert version_info >= (3, 0)
    prog_name = argv[0]
    main(argv[1:])
