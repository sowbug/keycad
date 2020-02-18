#!/usr/bin/env python3

import argparse
import json
import subprocess

import pcbnew
from skidl import *

KC_TO_MM = 1000000

# KiCad explodes with raw quote
# freerouting.jar explodes with raw backtick
SYMBOL_TO_ALNUM = {
    "'": 'quote',
    "`": 'backtick',
    "↑": 'up',
    "↓": 'down',
    "←": 'left',
    "→": 'right',
}

PCB_FILENAME = "keycad.kicad_pcb"
KINJECTOR_JSON_FILENAME = "keycad-kinjector.json"
NETLIST_FILENAME = "keycad.net"


class Pcb:
    def __init__(self, mx_key_width):
        self.__mx_key_width = mx_key_width
        self.__logical_key_width = 1
        self.__key_cursor_x = 0
        self.__key_cursor_y = 0
        self.reset_key_attributes()

        self.__kinjector_json = {}

    def set_logical_key_width(self, width):
        self.__logical_key_width = width

    def reset_key_attributes(self):
        self.__logical_key_width = 1

    def get_part_position(self):
        x = int((self.__key_cursor_x +
                 ((self.__logical_key_width - 1) * self.__mx_key_width / 2)))
        y = int(self.__key_cursor_y)
        return (x, y)

    def advance_cursor(self, end_of_row=False):
        self.__key_cursor_x += self.__mx_key_width * self.__logical_key_width
        self.reset_key_attributes()

    def cursor_carriage_return(self):
        self.__key_cursor_x = 0
        self.__key_cursor_y += self.__mx_key_width

    def mark_component_position(self, part, x_offset, y_offset, angle, side):
        x, y = self.get_part_position()
        self.__kinjector_json[part.ref] = {
            'position': {
                'x': (x + x_offset) * KC_TO_MM,
                'y': (y + y_offset) * KC_TO_MM,
                'angle': angle,
                'side': side
            }
        }

    def mark_switch_position(self, part):
        self.mark_component_position(part, 0, 0, 180, 'top')

    def mark_diode_position(self, part):
        x_offset, y_offset = (5, -self.__mx_key_width / 5)
        self.mark_component_position(part, x_offset, y_offset, 90, 'bottom')

    def mark_led_position(self, part):
        x_offset, y_offset = (0, -self.__mx_key_width / 4)
        self.mark_component_position(part, x_offset, y_offset, 0, 'bottom')

    def mark_pro_micro_position(self, part):
        x, y = 30, -50
        self.mark_component_position(part, x, y, 0, 'top')

    def mark_reset_switch_position(self, part):
        x, y = 50, -50
        self.mark_component_position(part, x, y, 0, 'top')

    def get_kinjector_dict(self):
        return self.__kinjector_json

    def place_pro_micro(self):
        pro_micro = Part('keycad',
                         'ProMicro',
                         NETLIST,
                         footprint='keycad:ArduinoProMicro')
        pro_micro.ref = 'U1'
        pro_micro.value = 'Pro Micro'
        self.mark_pro_micro_position(pro_micro)
        return pro_micro

    def place_reset_switch(self):
        reset = Part('keycad',
                     'SW_Push',
                     NETLIST,
                     footprint='keycad:SW_SPST_SKQG_WithoutStem')
        reset.ref = 'SW1'
        reset.value = 'SKQGAKE010'
        self.mark_reset_switch_position(reset)
        return reset


class KeyCad:
    def __init__(self, pcb):
        self.__row_index = 0
        self.__col_index = 0
        self.__keysw_partno = 1
        self.__d_partno = 1
        self.__led_partno = 1
        self.__key_matrix_rows = []
        self.__key_matrix_cols = []

        self.__pcb = pcb

        self.__vcc = Net('VCC')
        self.__gnd = Net('GND')

        self.__led_din_pin = None
        self.__led_dout_pin = None

        self.__key_matrix_x = 0
        self.__key_matrix_y = 0

    def process_row_metadata(self, metadata):
        pass

    def process_key_metadata(self, metadata):
        if 'w' in metadata:
            self.__pcb.set_logical_key_width(float(metadata['w']))

    def get_key_name(self, kle_name):
        parts = kle_name.split("\n")
        if len(parts) > 1:
            kle_name = parts[len(parts) - 1]
        if kle_name in SYMBOL_TO_ALNUM:
            return SYMBOL_TO_ALNUM[kle_name]
        return kle_name

    def create_keyswitch(self, key):
        # keyboard_parts.lib is found at https://github.com/tmk/kicad_lib_tmk
        part = Part('keycad',
                    'KEYSW',
                    NETLIST,
                    footprint='keycad:Kailh_socket_MX')
        part.ref = "K%d" % (self.__keysw_partno)
        part.value = self.get_key_name(str(key))
        self.__keysw_partno += 1
        self.__pcb.mark_switch_position(part)
        return part

    def create_diode(self):
        part = Part('keycad', 'D', NETLIST, footprint='keycad:D_0805')
        part.ref = "D%d" % (self.__d_partno)
        part.value = "1N4148"
        self.__d_partno += 1
        self.__pcb.mark_diode_position(part)
        return part

    def create_per_key_led(self):
        part = Part('keycad',
                    'SK6812MINI-E',
                    NETLIST,
                    footprint='keycad:SK6812-MINI-E-BOTTOM')
        part.ref = "LED%d" % (self.__led_partno)
        part.value = "SK6812MINI-E"
        self.__led_partno += 1
        self.__pcb.mark_led_position(part)
        return part

    def connect_per_key_led(self, led):
        self.__vcc += led[1]
        self.__gnd += led[3]

        if self.__led_din_pin is None:
            self.__led_din_pin = led[4]
        if self.__led_dout_pin is None:
            self.__led_dout_pin = led[2]
        led[4] += self.__led_dout_pin
        led[4].net.name = "%s_DIN" % led.ref
        self.__led_dout_pin = led[2]

    def process_key(self, key):
        keysw_part = self.create_keyswitch(key)
        d_part = self.create_diode()
        led_part = self.create_per_key_led()

        net = Net("%s_%s" % (keysw_part.ref, d_part.ref))
        net += keysw_part[2], d_part[2]

        self.connect_per_key_led(led_part)

        self.__key_matrix_rows[self.__key_matrix_x] += d_part[1]
        self.__key_matrix_cols[self.__key_matrix_y] += keysw_part[1]

        self.__key_matrix_x += 1
        if self.__key_matrix_x >= len(self.__key_matrix_cols):
            self.__key_matrix_x = 0
            self.__key_matrix_y += 1

    def create_matrix_nets(self):
        # TODO(miket): calculate right number
        for y in range(0, 9):
            self.__key_matrix_rows.append(Net("row%d" % y))
        for x in range(0, 9):
            self.__key_matrix_cols.append(Net("col%d" % x))

    def process_row(self, row):
        self.__col_index = 0
        for key in row:
            if isinstance(key, dict):
                self.process_key_metadata(key)
            else:
                self.process_key(key)
                self.__col_index += 1
                self.__pcb.advance_cursor()

    def handle_kle_json(self, json):
        self.create_matrix_nets()
        for row in kle_json:
            if isinstance(row, dict):
                self.process_row_metadata(row)
            else:
                self.process_row(row)
                self.__row_index += 1
                self.__pcb.cursor_carriage_return()

    def connect_pro_micro(self, pro_micro):
        PRO_MICRO_GPIOS = [
            1, 2, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
        ]

        next_pin_index = 0
        self.__gnd += pro_micro[3], pro_micro[4], pro_micro[23]
        self.__vcc += pro_micro[21]

        if self.__led_din_pin is not None:
            pro_micro[5] += self.__led_din_pin 
        else:
            # TODO(miket): change to a method that allows asking for the
            # next GPIO, and then this can be refactored away
            PRO_MICRO_GPIOS.append(5)

        for row in self.__key_matrix_rows:
            if len(row) == 0:
                self.__key_matrix_rows.remove(row)
        for col in self.__key_matrix_cols:
            if len(col) == 0:
                self.__key_matrix_cols.remove(col)

        if False and len(self.__key_matrix_rows) + len(
                self.__key_matrix_cols) > len(PRO_MICRO_GPIOS):
            print(
                "ERROR: need pins to connect %d rows and %d cols but have only %d GPIOs"
                % (len(self.__key_matrix_rows), len(
                    self.__key_matrix_cols), len(PRO_MICRO_GPIOS)))
            sys.exit(1)
        for row in self.__key_matrix_rows:
            print(row, len(row))
            row += pro_micro[PRO_MICRO_GPIOS[next_pin_index]]
            next_pin_index += 1
        for col in self.__key_matrix_cols:
            print(col, len(col))
            col += pro_micro[PRO_MICRO_GPIOS[next_pin_index]]
            next_pin_index += 1

    def connect_reset_switch(self, reset, pro_micro):
        self.__gnd += reset[2]
        pro_micro[22] += reset[1]
        reset[1].net.name = "RST"

    def set_next_dout_pin(self, next_dout_pin):
        self.__next_dout_pin = next_dout_pin


parser = argparse.ArgumentParser(
    description=
    'Generate keyboard manufacturing files from www.keyboard-layout-editor.com JSON.'
)
parser.add_argument('kle_json_filename', help='KLE JSON filename')
args = parser.parse_args()

pcb = Pcb(19.05)
keycad = KeyCad(pcb)

json_text = open(args.kle_json_filename, "r").read()
kle_json = json.loads(json_text)
keycad.handle_kle_json(kle_json)

pro_micro = pcb.place_pro_micro()
keycad.connect_pro_micro(pro_micro)
reset = pcb.place_reset_switch()
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
