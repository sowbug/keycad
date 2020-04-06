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
            # This is taken from the JD40 preset layout on http://www.keyboard-layout-editor.com/
            json.loads('''
[["Esc","Q","W","E","R","T","Y","U","I","O","P","Back<br>Space"],
[{"w":1.25},"Tab","A","S","D","F","G","H","J","K","L",{"w":1.75},"Enter"],
[{"w":1.75},"Shift","Z","X","C","V","B","N","M","<\\n.",{"w":1.25},"Shift","Fn"],
[{"w":1.25},"Hyper","Super","Meta",{"a":7,"w":6.25},"",{"a":4,"w":1.25},"Meta",{"w":1.25},"Super"]]
'''))

        builder = BoardBuilder(parser, schematic)
        builder.build(add_pro_micro=False, add_blue_pill=True)

        gnd = Net.get("GND")
        self.assertEqual(gnd.name, "GND")
        vcc = Net.get("VCC")
        self.assertEqual(vcc.name, "VCC")

        # Is the Blue Pill correctly connected?
        mcu = Part.get("U2")[0]
        expected_mcu_nets = [
            None,  # 1, VBAT - RTC backup, not used by us
            None,  # 2, PC_13 - LED
            "ROW_1",
            "ROW_2",
            "ROW_3",
            "ROW_4",
            "COL_1",
            "COL_2",
            "COL_3",
            "COL_4",  # 10
            "COL_5",
            "COL_6",
            "COL_7",
            "COL_8",
            "COL_9",
            "COL_10",
            None,  # 17, NRST
            None,  # 18, 3V3
            "GND",
            "GND",  # 20
            "COL_11",
            "COL_12",
            None,  # 23, PB14
            None,  # 24, PB15
            None,  # 25, PA8
            None,  # 26, PA9
            None,  # 27, PA10
            "USB_DM",
            "USB_DP",
            None,  # 30, PA15
            None,  # 31, PB3
            None,  # 32, PB4
            None,  # 33, PB5
            None,  # 34, PB6
            None,  # 35, PB7
            None,  # 36, PB8
            "LED_DATA",  # 37, PB9
            "VCC",
            "GND",
            None  # 40, 3V3
        ]
        self.assertEqual(len(expected_mcu_nets), 40)
        pin_no = 1
        for name in expected_mcu_nets:
            if name is not None:
                self.assertEqual(
                    mcu[pin_no].net.name, name,
                    "Expected pin %d to have net %s but it had %s" %
                    (pin_no, name, mcu[pin_no].net.name))
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
                self.assertEqual(part[4].net.name, expected_mcu_nets[37 - 1])
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

        # Is each keyswitch connected properly?
        expected_rows = 4
        expected_cols = [12, 11, 11, 6]
        current_row = 1
        current_col = 1
        key_no = 1
        for i in range(1, parser.key_count + 1):
            part = Part.get("K%d" % i)[0]
            diode_part = Part.get("D%d" % i)[0]

            # For COL2ROW, flow should be COL GPIO, switch, diode, ROW GPIO,
            # and the diode's arrow should be pointing toward the ROW GPIO.
            #
            # The first keyswitch pin should be connected to a COL_ GPIO.
            self.assertEqual(part[1].net.name, "COL_%d" % current_col)

            # The second pin should be connected to the anode of a diode.
            self.assertEqual(part[2].net.name, "K%d_D%d" % (key_no, key_no))

            # The diode's anode should be connected to the keyswitch.
            self.assertEqual(diode_part[2].net.name,
                             "K%d_D%d" % (key_no, key_no))

            # The diode's cathode should be connected to a ROW_ GPIO.
            self.assertEqual(diode_part[1].net.name, "ROW_%d" % current_row)

            key_no += 1
            current_col += 1
            if current_col > expected_cols[current_row - 1]:
                current_row += 1
                current_col = 1
        self.assertEqual(current_row, expected_rows + 1)

        # Is the USB-C connector connected properly?
        part = Part.get("J1")[0]

        # Power
        self.assertEqual(part["A1"].net.name, "GND")
        self.assertEqual(part["A12"].net.name, "GND")
        self.assertEqual(part["B1"].net.name, "GND")
        self.assertEqual(part["B12"].net.name, "GND")
        self.assertEqual(part["A4"].net.name, "VCC")
        self.assertEqual(part["A9"].net.name, "VCC")
        self.assertEqual(part["B4"].net.name, "VCC")
        self.assertEqual(part["B9"].net.name, "VCC")

        # Data
        self.assertEqual(part["A6"].net.name, expected_mcu_nets[29 - 1])
        self.assertEqual(part["B6"].net.name, expected_mcu_nets[29 - 1])
        self.assertEqual(part["A7"].net.name, expected_mcu_nets[28 - 1])
        self.assertEqual(part["B7"].net.name, expected_mcu_nets[28 - 1])

        # Channel Configuration: tie CC1/CC2 to GND via 5.1k resistors
        self.assertEqual(part["A5"].net.name, "CC1")
        self.assertEqual(part["B5"].net.name, "CC2")

        r1 = Part.get("R1")[0]
        r2 = Part.get("R2")[0]
        self.assertEqual(r1.value, "5K1")
        self.assertEqual(r2.value, "5K1")
        self.assertEqual(r1[1].net.name, "CC1")
        self.assertEqual(r2[1].net.name, "CC2")
        self.assertEqual(r1[2].net.name, "GND")
        self.assertEqual(r2[2].net.name, "GND")