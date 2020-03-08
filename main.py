#!/usr/bin/env python3

import argparse
import json
import os
import subprocess

import pcbnew
from skidl import generate_netlist

KC_TO_MM = 1000000

from keycad import kle
from keycad import pcb
from keycad import schematic

PCB_FILENAME = "keycad.kicad_pcb"
KINJECTOR_JSON_FILENAME = "keycad-kinjector.json"
NETLIST_FILENAME = "keycad.net"


def main():
    parser = argparse.ArgumentParser(
        description=
        'Generate keyboard manufacturing files from www.keyboard-layout-editor.com JSON.'
    )
    parser.add_argument('kle_json_filename', help='KLE JSON filename')
    parser.add_argument('--position_json_filename',
                        help='kinjector-format overrides of positions')
    parser.add_argument('--out_dir', help='directory to place output files')
    args = parser.parse_args()

    kbd_pcb = pcb.Pcb(19.05)
    if args.position_json_filename is not None:
        kbd_pcb.read_positions(args.position_json_filename)
    if args.out_dir is not None:
        cwd = args.out_dir
    else:
        cwd = os.getcwd()

    kbd_schematic = schematic.Schematic(kbd_pcb)

    kle_json_parser = kle.Parser()
    kle_json_parser.load(args.kle_json_filename)
    for key in kle_json_parser.keys:
        kbd_schematic.add_key(key)

    pro_micro = kbd_schematic.create_pro_micro()
    kbd_schematic.connect_pro_micro(pro_micro)
    reset = kbd_schematic.create_reset_switch()
    kbd_schematic.connect_reset_switch(reset, pro_micro)

    with open(os.path.join(cwd, NETLIST_FILENAME), "w") as f:
        generate_netlist(file_=f)

    with open(os.path.join(cwd, KINJECTOR_JSON_FILENAME), "w") as f:
        f.write(
            json.dumps({'board': {
                'modules': kbd_pcb.get_kinjector_dict()
            }},
                       sort_keys=True,
                       indent=4))

    subprocess.call([
        'kinet2pcb', '--nobackup', '--overwrite', '-i',
        os.path.join(cwd, NETLIST_FILENAME), '-w'
    ])
    subprocess.call([
        'kinjector', '--nobackup', '--overwrite', '--from',
        os.path.join(cwd, KINJECTOR_JSON_FILENAME), '--to',
        os.path.join(cwd, PCB_FILENAME)
    ])

    kbd_pcb = pcbnew.LoadBoard(os.path.join(cwd, PCB_FILENAME))
    kbd_pcb.ComputeBoundingBox(False)
    l, t, r, b = kbd_pcb.GetBoundingBox().GetLeft(), kbd_pcb.GetBoundingBox().GetTop(
    ), kbd_pcb.GetBoundingBox().GetRight(), kbd_pcb.GetBoundingBox().GetBottom()

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
    draw_segment(kbd_pcb, POINTS[0][0] + CORNER_RADIUS, POINTS[0][1],
                 POINTS[1][0] - CORNER_RADIUS, POINTS[1][1])
    draw_segment(kbd_pcb, POINTS[1][0], POINTS[1][1] + CORNER_RADIUS, POINTS[2][0],
                 POINTS[2][1] - CORNER_RADIUS)
    draw_segment(kbd_pcb, POINTS[2][0] - CORNER_RADIUS, POINTS[2][1],
                 POINTS[3][0] + CORNER_RADIUS, POINTS[3][1])
    draw_segment(kbd_pcb, POINTS[3][0], POINTS[3][1] - CORNER_RADIUS, POINTS[0][0],
                 POINTS[0][1] + CORNER_RADIUS)

    draw_arc(kbd_pcb, POINTS[0][0] + CORNER_RADIUS, POINTS[0][1] + CORNER_RADIUS,
             POINTS[0][0], POINTS[0][1] + CORNER_RADIUS, 90)
    draw_arc(kbd_pcb, POINTS[1][0] - CORNER_RADIUS, POINTS[1][1] + CORNER_RADIUS,
             POINTS[1][0] - CORNER_RADIUS, POINTS[1][1], 90)
    draw_arc(kbd_pcb, POINTS[2][0] - CORNER_RADIUS, POINTS[2][1] - CORNER_RADIUS,
             POINTS[2][0], POINTS[2][1] - CORNER_RADIUS, 90)
    draw_arc(kbd_pcb, POINTS[3][0] + CORNER_RADIUS, POINTS[3][1] - CORNER_RADIUS,
             POINTS[3][0] + CORNER_RADIUS, POINTS[3][1], 90)

    layertable = {}

    numlayers = pcbnew.PCB_LAYER_ID_COUNT
    for i in range(numlayers):
        layertable[kbd_pcb.GetLayerName(i)] = i

    nets = kbd_pcb.GetNetsByName()

    powernets = []

    for name in ["GND"]:
        if (nets.has_key(name)):
            powernets.append((name, "F.Cu"))
            powernets.append((name, "B.Cu"))
            break

    for netname, layername in (powernets):
        net = nets.find(netname).value()[1]
        layer = layertable[layername]
        newarea = kbd_pcb.InsertArea(
            net.GetNet(), 0, layer, l, t, pcbnew.ZONE_EXPORT_VALUES
        )  # picked random name because ZONE_HATCH_STYLE_DIAGONAL_EDGE was missing

        newoutline = newarea.Outline()
        newoutline.Append(l, b)
        newoutline.Append(r, b)
        newoutline.Append(r, t)
        newarea.Hatch()

    filler = pcbnew.ZONE_FILLER(kbd_pcb)
    zones = kbd_pcb.Zones()
    filler.Fill(zones)

    pcbnew.SaveBoard(os.path.join(cwd, PCB_FILENAME), kbd_pcb)

    os.unlink(os.path.join(cwd, KINJECTOR_JSON_FILENAME))

    subprocess.call(['xdg-open', os.path.join(cwd, PCB_FILENAME)])


if __name__ == "__main__":
    main()
