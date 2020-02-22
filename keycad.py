#!/usr/bin/env python3

import argparse
import os
import json
import subprocess

import pcbnew
from skidl import generate_netlist

import kle_json
from pcb import Pcb
from schematic import KeyCad

KC_TO_MM = 1000000

PCB_FILENAME = "keycad.kicad_pcb"
KINJECTOR_JSON_FILENAME = "keycad-kinjector.json"
NETLIST_FILENAME = "keycad.net"

parser = argparse.ArgumentParser(
    description=
    'Generate keyboard manufacturing files from www.keyboard-layout-editor.com JSON.'
)
parser.add_argument('kle_json_filename', help='KLE JSON filename')
parser.add_argument('--position_json_filename',
                    help='kinjector-format overrides of positions')
args = parser.parse_args()

pcb = Pcb(19.05)
if args.position_json_filename is not None:
    pcb.read_positions(args.position_json_filename)

kle_json_parser = kle_json.Parser()
kle_json_parser.load(args.kle_json_filename)

keycad = KeyCad(pcb)

pro_micro = keycad.create_pro_micro()
keycad.connect_pro_micro(pro_micro)
reset = keycad.create_reset_switch()
keycad.connect_reset_switch(reset, pro_micro)

with open(NETLIST_FILENAME, "w") as f:
    generate_netlist(file_=f)

f = open(KINJECTOR_JSON_FILENAME, "w")
f.write(
    json.dumps({'board': {
        'modules': pcb.get_kinjector_dict()
    }},
               sort_keys=True,
               indent=4))
f.close()

subprocess.call(
    ['kinet2pcb', '--nobackup', '--overwrite', '-i', NETLIST_FILENAME, '-w'])
subprocess.call([
    'kinjector', '--nobackup', '--overwrite', '--from',
    KINJECTOR_JSON_FILENAME, '--to', PCB_FILENAME
])

pcb = pcbnew.LoadBoard(PCB_FILENAME)
pcb.ComputeBoundingBox(False)
l, t, r, b = pcb.GetBoundingBox().GetLeft(), pcb.GetBoundingBox().GetTop(
), pcb.GetBoundingBox().GetRight(), pcb.GetBoundingBox().GetBottom()


def draw_segment(board, x1, y1, x2, y2):
    layer = pcbnew.Edge_Cuts
    thickness = 0.15 * pcbnew.IU_PER_MM
    ds = pcbnew.DRAWSEGMENT(board)
    ds.SetLayer(layer)
    ds.SetWidth(max(1, int(thickness)))
    board.Add(ds)
    ds.SetStart(pcbnew.wxPoint(x1, y1))
    ds.SetEnd(pcbnew.wxPoint(x2, y2))


def draw_arc(board, cx, cy, sx, sy, a):
    layer = pcbnew.Edge_Cuts
    thickness = 0.15 * pcbnew.IU_PER_MM
    ds = pcbnew.DRAWSEGMENT(board)
    ds.SetLayer(layer)
    ds.SetWidth(max(1, int(thickness)))
    board.Add(ds)
    ds.SetShape(pcbnew.S_ARC)
    ds.SetCenter(pcbnew.wxPoint(cx, cy))
    ds.SetArcStart(pcbnew.wxPoint(sx, sy))
    ds.SetAngle(a * 10)


MARGIN = 0 * KC_TO_MM
CORNER_RADIUS = 3 * KC_TO_MM
POINTS = [
    (l - MARGIN, t - MARGIN),
    (r + MARGIN, t - MARGIN),
    (r + MARGIN, b + MARGIN),
    (l - MARGIN, b + MARGIN),
]
draw_segment(pcb, POINTS[0][0] + CORNER_RADIUS, POINTS[0][1],
             POINTS[1][0] - CORNER_RADIUS, POINTS[1][1])
draw_segment(pcb, POINTS[1][0], POINTS[1][1] + CORNER_RADIUS, POINTS[2][0],
             POINTS[2][1] - CORNER_RADIUS)
draw_segment(pcb, POINTS[2][0] - CORNER_RADIUS, POINTS[2][1],
             POINTS[3][0] + CORNER_RADIUS, POINTS[3][1])
draw_segment(pcb, POINTS[3][0], POINTS[3][1] - CORNER_RADIUS, POINTS[0][0],
             POINTS[0][1] + CORNER_RADIUS)

draw_arc(pcb, POINTS[0][0] + CORNER_RADIUS, POINTS[0][1] + CORNER_RADIUS,
         POINTS[0][0], POINTS[0][1] + CORNER_RADIUS, 90)
draw_arc(pcb, POINTS[1][0] - CORNER_RADIUS, POINTS[1][1] + CORNER_RADIUS,
         POINTS[1][0] - CORNER_RADIUS, POINTS[1][1], 90)
draw_arc(pcb, POINTS[2][0] - CORNER_RADIUS, POINTS[2][1] - CORNER_RADIUS,
         POINTS[2][0], POINTS[2][1] - CORNER_RADIUS, 90)
draw_arc(pcb, POINTS[3][0] + CORNER_RADIUS, POINTS[3][1] - CORNER_RADIUS,
         POINTS[3][0] + CORNER_RADIUS, POINTS[3][1], 90)

layertable = {}

numlayers = pcbnew.PCB_LAYER_ID_COUNT
for i in range(numlayers):
    layertable[pcb.GetLayerName(i)] = i

nets = pcb.GetNetsByName()

powernets = []

for name in ["GND"]:
    if (nets.has_key(name)):
        powernets.append((name, "F.Cu"))
        powernets.append((name, "B.Cu"))
        break

for netname, layername in (powernets):
    net = nets.find(netname).value()[1]
    layer = layertable[layername]
    newarea = pcb.InsertArea(
        net.GetNet(), 0, layer, l, t, pcbnew.ZONE_EXPORT_VALUES
    )  # picked random name because ZONE_HATCH_STYLE_DIAGONAL_EDGE was missing

    newoutline = newarea.Outline()
    newoutline.Append(l, b)
    newoutline.Append(r, b)
    newoutline.Append(r, t)
    newarea.Hatch()

filler = pcbnew.ZONE_FILLER(pcb)
zones = pcb.Zones()
filler.Fill(zones)

pcbnew.SaveBoard(PCB_FILENAME, pcb)

os.unlink(KINJECTOR_JSON_FILENAME)

subprocess.call(['xdg-open', PCB_FILENAME])
