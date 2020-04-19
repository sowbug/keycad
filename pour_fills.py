#!/usr/bin/env python3

import argparse
import os
import subprocess

from keycad.kicad import pour_fills_on_board


def main():
    arg_parser = argparse.ArgumentParser(
        description="Pour GND fills on both sides of Kicad PCB.")
    arg_parser.add_argument("kicad_pcb_filename", help="Kicad PCB filename")
    args = arg_parser.parse_args()

    pour_fills_on_board(args.kicad_pcb_filename)


if __name__ == "__main__":
    main()
