import json
import unittest

from skidl import Net, Part

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
        parser.handle_dict(
            json.loads('''
[["Esc","Q","W","E","R","T","Y","U","I","O","P","Back<br>Space"],
[{"w":1.25},"Tab","A","S","D","F","G","H","J","K","L",{"w":1.75},"Enter"],
[{"w":1.75},"Shift","Z","X","C","V","B","N","M","<\\n.",{"w":1.25},"Shift","Fn"],
[{"w":1.25},"Hyper","Super","Meta",{"a":7,"w":6.25},"",{"a":4,"w":1.25},"Meta",{"w":1.25},"Super"]]
'''))

        builder = BoardBuilder(parser, schematic)
        builder.build(add_pro_micro=False, add_blue_pill=True)

        #kbd_dict["matrix_pins"] = schematic.get_legend_dict()
        gnd = Net.get("GND")
        self.assertEqual(gnd.name, "GND")
        vcc = Net.get("VCC")
        self.assertEqual(vcc.name, "VCC")

        # Is the Blue Pill correctly connected?
        mcu = Part.get("U2")[0]
        expected_net_names = [
            None,  # 1
            None,
            "ROW_0",
            "ROW_1",
            "ROW_2",
            "ROW_3",
            "ROW_4",
            "ROW_5",
            "ROW_6",
            "ROW_7",  # 10
            "ROW_8",
            "COL_0",
            "COL_1",
            "COL_2",
            "COL_3",
            "COL_4",
            None,
            None,
            "GND",
            "GND",  # 20
            "COL_6",
            "COL_8",
            None,
            None,
            None,
            None,
            None,
            "USB_DM",
            "USB_DP",
            None,  # 30
            None,
            None,
            None,
            None,
            None,
            None,
            "LED_DATA",
            "VCC",
            "GND",
            None  # 40
        ]
        self.assertEqual(len(expected_net_names), 40)
        pin_no = 1
        for name in expected_net_names:
            if name is not None:
                self.assertEqual(mcu[pin_no].net.name, name)
            else:
                self.assertIsNone(mcu[pin_no].net)
            pin_no += 1

        # Are all the LEDs connected correctly?
        for i in range(1, parser.key_count + 1):
            is_first = i == 1
            is_last = i == parser.key_count
            part = Part.get("LED%d" % i)[0]
            self.assertEqual(part[1].net.name, "VCC")
            interconnect_net_name_in = "LED%d_DIN" % (i)
            interconnect_net_name_out = "LED%d_DIN" % (i + 1)
            if is_last:
                self.assertIsNone(part[2].net)
            else:
                self.assertEqual(part[2].net.name, interconnect_net_name_out)
            self.assertEqual(part[3].net.name, "GND")
            if is_first:
                self.assertEqual(part[4].net.name, expected_net_names[37 - 1])
            else:
                self.assertEqual(part[4].net.name, interconnect_net_name_in)

        # Are all the LED nets connected to exactly two things?
        # (Except the last one)
        for i in range(1, parser.key_count + 1):
            part = Part.get("LED%d" % i)[0]
            self.assertEqual(len(part[4].nets[0]), 2)
            if i == parser.key_count:
                self.assertEqual(len(part[2].nets), 0)
            else:
                self.assertEqual(len(part[2].nets[0]), 2)
