import unittest

from keycad import builder
from keycad.builder import BoardBuilder
from keycad.kicad import draw_outline, generate_kicad_pcb
from keycad.kle import Parser
from keycad.manual import Manual
from keycad.pcb import Pcb
from keycad.schematic import Schematic


class TestBuilder(unittest.TestCase):
    def test_netlists(self):
        pcb = Pcb(19.05, 19.05)

    schematic = Schematic(pcb)

    parser = Parser()
    parser.load(args.kle_json_filename)

    builder = BoardBuilder(parser, schematic)
    builder.build(add_pro_micro=args.add_pro_micro,
                  add_blue_pill=args.add_blue_pill)
    kbd_dict["matrix_pins"] = schematic.get_legend_dict()
