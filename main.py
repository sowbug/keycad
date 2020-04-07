#!/usr/bin/env python3

import argparse
import json
import os
import subprocess

from skidl import generate_netlist

from keycad.builder import BoardBuilder
from keycad.kicad import draw_outline, draw_keepout, generate_kicad_pcb
from keycad.kle import Parser
from keycad.manual import Manual
from keycad.pcb import Pcb
from keycad.schematic import Schematic

PCB_FILENAME_SUFFIX = ".kicad_pcb"
NETLIST_FILENAME_SUFFIX = ".net"
USER_GUIDE_SUFFIX = "-user-guide.md"

KINJECTOR_JSON_FILENAME = "keycad-kinjector.json"


def main():
    arg_parser = argparse.ArgumentParser(
        description=
        "Generate keyboard manufacturing files from www.keyboard-layout-editor.com JSON."
    )
    arg_parser.add_argument("kle_json_filename", help="KLE JSON filename")
    arg_parser.add_argument("--position_json_filename",
                            help="kinjector-format overrides of positions")
    arg_parser.add_argument("--output_prefix",
                            help="prefix for output filenames",
                            default="my-keyboard")
    arg_parser.add_argument("--out_dir",
                            help="directory to place output files",
                            default="output")
    arg_parser.add_argument("--add_pro_micro",
                            help="whether to add Pro Micro to board",
                            action="store_true")
    arg_parser.add_argument("--add_blue_pill",
                            help="whether to add Blue Pill to board",
                            action="store_true")
    arg_parser.add_argument(
        "--use_pg1350",
        help="whether to use Kailh Choc PG1350 instead of Cherry MX",
        action="store_true")
    arg_parser.add_argument(
        "--no_hotswap",
        help="whether to use soldered sockets instead of Kailh hotswap sockets",
        action="store_true")
    args = arg_parser.parse_args()

    kbd_dict = {
        "args": str(args),
    }

    if args.use_pg1350:
        key_width = 18
        key_height = 17
    else:
        key_width = 19.05
        key_height = 19.05
    pcb = Pcb(key_width, key_height)

    kbd_dict["keyswitch_width_mm"] = key_width
    kbd_dict["keyswitch_height_mm"] = key_height

    if args.position_json_filename is not None:
        pcb.read_positions(args.position_json_filename)
    if args.out_dir is not None:
        out_dir = args.out_dir
        os.makedirs(out_dir, exist_ok=True)
    else:
        out_dir = os.getcwd()

    pcb_filename = os.path.join(out_dir,
                                args.output_prefix + PCB_FILENAME_SUFFIX)
    pcb_sandwich_bottom_filename = os.path.join(
        out_dir, args.output_prefix + "-bottom" + PCB_FILENAME_SUFFIX)
    pcb_sandwich_plate_filename = os.path.join(
        out_dir, args.output_prefix + "-top" + PCB_FILENAME_SUFFIX)
    netlist_filename = os.path.join(
        out_dir, args.output_prefix + NETLIST_FILENAME_SUFFIX)
    user_guide_filename = os.path.join(out_dir,
                                       args.output_prefix + USER_GUIDE_SUFFIX)

    schematic = Schematic(pcb, not args.use_pg1350, not args.no_hotswap)

    parser = Parser()
    parser.load(args.kle_json_filename)

    builder = BoardBuilder(parser, schematic)
    builder.build(add_pro_micro=args.add_pro_micro,
                  add_blue_pill=args.add_blue_pill)
    kbd_dict["matrix_pins"] = schematic.get_legend_dict()

    with open(netlist_filename, "w") as f:
        generate_netlist(file_=f)

    pcb.write_kinjector_file(os.path.join(out_dir, KINJECTOR_JSON_FILENAME))
    generate_kicad_pcb(netlist_filename,
                       os.path.join(out_dir, KINJECTOR_JSON_FILENAME),
                       pcb_filename)

    board_width = parser.board_right - parser.board_left
    board_height = parser.board_bottom - parser.board_top
    kbd_dict["pcb_width_mm"] = board_width
    kbd_dict["pcb_height_mm"] = board_height

    if args.add_blue_pill:
        # TODO(miket): this is a horrible hack.
        usb_cutout_position = 14.375 * key_width
        usb_cutout_width = 4.7 * 2
    else:
        usb_cutout_position = -1
        usb_cutout_width = -1
    draw_outline(pcb_filename,
                 -key_width / 2,
                 -key_height / 2,
                 board_width * key_width,
                 board_height * key_height,
                 usb_cutout_position=usb_cutout_position,
                 usb_cutout_width=usb_cutout_width)
    draw_keepout(pcb_filename, usb_cutout_position - usb_cutout_width / 2, -9.525,
                 usb_cutout_width, 6.1)
    draw_outline(pcb_sandwich_bottom_filename,
                 -key_width / 2,
                 -key_height / 2,
                 board_width * key_width,
                 board_height * key_height,
                 modify_existing=False,
                 margin_mm=5,
                 corner_radius_mm=5)
    draw_outline(pcb_sandwich_plate_filename,
                 -key_width / 2,
                 -key_height / 2,
                 board_width * key_width,
                 board_height * key_height,
                 modify_existing=False,
                 margin_mm=5,
                 corner_radius_mm=5)

    os.unlink(os.path.join(out_dir, KINJECTOR_JSON_FILENAME))

    manual = Manual(kbd_dict)
    manual.generate(user_guide_filename)

    subprocess.call(["xdg-open", pcb_filename])


if __name__ == "__main__":
    main()
