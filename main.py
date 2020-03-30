#!/usr/bin/env python3

import argparse
import json
import os
import subprocess

from skidl import generate_netlist

from keycad.builder import BoardBuilder
from keycad.kicad import draw_outline, generate_kicad_pcb
from keycad.kle import Parser
from keycad.pcb import Pcb
from keycad.schematic import Schematic

PCB_FILENAME = "keycad.kicad_pcb"
KINJECTOR_JSON_FILENAME = "keycad-kinjector.json"
NETLIST_FILENAME = "keycad.net"


def main():
    arg_parser = argparse.ArgumentParser(
        description=
        "Generate keyboard manufacturing files from www.keyboard-layout-editor.com JSON."
    )
    arg_parser.add_argument("kle_json_filename", help="KLE JSON filename")
    arg_parser.add_argument("--position_json_filename",
                            help="kinjector-format overrides of positions")
    arg_parser.add_argument("--out_dir",
                            help="directory to place output files")
    arg_parser.add_argument("--add_pro_micro",
                            help="whether to add Pro Micro to board",
                            action="store_true")
    arg_parser.add_argument("--add_blue_pill",
                            help="whether to add Blue Pill to board",
                            action="store_true")
    args = arg_parser.parse_args()

    pcb = Pcb(19.05)

    if args.position_json_filename is not None:
        pcb.read_positions(args.position_json_filename)
    if args.out_dir is not None:
        out_dir = args.out_dir
    else:
        out_dir = os.getcwd()

    schematic = Schematic(pcb)

    parser = Parser()
    parser.load(args.kle_json_filename)

    builder = BoardBuilder(parser, schematic)
    builder.build(add_pro_micro=args.add_pro_micro,
                  add_blue_pill=args.add_blue_pill)

    print(schematic.get_legend())

    with open(os.path.join(out_dir, NETLIST_FILENAME), "w") as f:
        generate_netlist(file_=f)

    pcb.write_kinjector_file(os.path.join(out_dir, KINJECTOR_JSON_FILENAME))
    generate_kicad_pcb(os.path.join(out_dir, NETLIST_FILENAME),
                       os.path.join(out_dir, KINJECTOR_JSON_FILENAME),
                       os.path.join(out_dir, PCB_FILENAME))

    draw_outline(os.path.join(out_dir, PCB_FILENAME))

    os.unlink(os.path.join(out_dir, KINJECTOR_JSON_FILENAME))

    subprocess.call(["xdg-open", os.path.join(out_dir, PCB_FILENAME)])


if __name__ == "__main__":
    main()
