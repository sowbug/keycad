#!/usr/bin/env python3

import argparse
import json
import os
import subprocess

from skidl import generate_netlist

from keycad.builder import BoardBuilder
from keycad.kicad import (add_keepout_to_board, add_labels_to_board,
                          add_outline_to_board, generate_kicad_pcb)
from keycad.kle import Parser
from keycad.manual import Manual
from keycad.pcb import Pcb
from keycad.schematic import Schematic
from keycad.partstore import PartStore

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
    arg_parser.add_argument("--descriptors_filename",
                            help="JSON file containing keyboard description")
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
        "--add_per_key_rgb",
        help="whether to add an RGB LED for each keyswitch",
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

    if args.descriptors_filename:
        with open(args.descriptors_filename, "r") as f:
            descriptors = json.loads(f.read())
            print(descriptors)
    else:
        descriptors = {
            "family_id": "keycad",
            "identifier": "generic_keyboard",
            "usb_vid": "0xFEED",
            "usb_pid": "0x0001",
            "usb_manufacturer": "Generic",
            "usb_product": "Generic",
            "usb_description": "A keyboard"
        }
    kbd_dict["descriptors"] = descriptors

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

    partstore = PartStore()
    schematic = Schematic(partstore, pcb, not args.use_pg1350,
                          not args.no_hotswap)

    parser = Parser()
    parser.load(args.kle_json_filename)

    builder = BoardBuilder(parser, schematic)
    builder.build(add_pro_micro=args.add_pro_micro,
                  add_blue_pill=args.add_blue_pill,
                  add_per_key_rgb=args.add_per_key_rgb)
    kbd_dict["matrix_pins"] = schematic.get_legend_dict()
    kbd_dict["kle"] = parser
    kbd_dict["key_matrix_keys"] = schematic.key_matrix_keys

    kbd_dict["has_per_key_led"] = True
    if schematic.led_data_pin_name is not None:
        kbd_dict["led_data_pin"] = schematic.led_data_pin_name
    kbd_dict["led_count"] = parser.key_count

    with open(netlist_filename, "w") as f:
        generate_netlist(file_=f)

    pcb.write_kinjector_file(os.path.join(out_dir, KINJECTOR_JSON_FILENAME))
    generate_kicad_pcb(netlist_filename,
                       os.path.join(out_dir, KINJECTOR_JSON_FILENAME),
                       pcb_filename)

    board_width = parser.board_right - parser.board_left
    board_height = parser.board_bottom - parser.board_top
    pcb_width_mm = board_width * key_width
    pcb_height_mm = board_height * key_height
    kbd_dict["pcb_width_mm"] = pcb_width_mm
    kbd_dict["pcb_height_mm"] = pcb_height_mm

    if args.add_blue_pill:
        KC_TO_MM = 1000000
        # J1 is a magic ref that means the USB-C connector
        position = pcb.get_part_position("J1")
        if position:
            usb_cutout_position = position["x"] / KC_TO_MM
            # Korean Hroparts TYPE-C-31-M-14
            usb_cutout_width = 4.7 * 2
    else:
        usb_cutout_position = -1
        usb_cutout_width = -1
    add_outline_to_board(pcb_filename,
                         -key_width / 2,
                         -key_height / 2,
                         pcb_width_mm,
                         pcb_height_mm,
                         usb_cutout_position=usb_cutout_position,
                         usb_cutout_width=usb_cutout_width)
    add_keepout_to_board(pcb_filename,
                         usb_cutout_position - usb_cutout_width / 2, -9.525,
                         usb_cutout_width, 6.1)
    add_outline_to_board(pcb_sandwich_bottom_filename,
                         -key_width / 2,
                         -key_height / 2,
                         pcb_width_mm,
                         pcb_height_mm,
                         modify_existing=False,
                         margin_mm=5,
                         corner_radius_mm=5)
    add_outline_to_board(pcb_sandwich_plate_filename,
                         -key_width / 2,
                         -key_height / 2,
                         pcb_width_mm,
                         pcb_height_mm,
                         modify_existing=False,
                         margin_mm=5,
                         corner_radius_mm=5)
    labels = []
    for key in parser.keys:
        labels.append(key.get_rowcol_label_dict(key_width, key_height))
    labels.append({
        "text": schematic.get_legend_text(),
        "x_mm": pcb_width_mm / 2,
        "y_mm": pcb_height_mm - key_height / 2 - 1
    })
    add_labels_to_board(pcb_filename, labels)

    os.unlink(os.path.join(out_dir, KINJECTOR_JSON_FILENAME))

    kbd_dict["bom"] = partstore.get_bom()

    manual = Manual(kbd_dict)
    manual.generate(user_guide_filename)

    subprocess.call(["xdg-open", pcb_filename])


if __name__ == "__main__":
    main()
