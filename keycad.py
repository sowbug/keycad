#!/usr/bin/env python3

import argparse
import json

from skidl import *

KC_TO_MM = 1000000


class Pcb:
    def __init__(self, mx_key_width):
        self.__mx_key_width = mx_key_width
        self.__logical_key_width = 1
        self.__key_cursor_x = 0
        self.__key_cursor_y = 0
        self.reset_key_attributes()

        self.__kinjector_json = {}

        self.__bounding_box_left = 1000
        self.__bounding_box_top = 1000
        self.__bounding_box_right = -1000
        self.__bounding_box_bottom = -1000

    def update_bounding_box(self, x, y):
        if self.__bounding_box_left > x:
            self.__bounding_box_left = x
        if self.__bounding_box_top > y:
            self.__bounding_box_top = y
        if self.__bounding_box_right < x:
            self.__bounding_box_right = x
        if self.__bounding_box_bottom < y:
            self.__bounding_box_bottom = y

    def get_bounding_box(self):
        return (self.__bounding_box_left, self.__bounding_box_top,
                self.__bounding_box_right, self.__bounding_box_bottom)

    def set_logical_key_width(self, width):
        self.__logical_key_width = width
        print("setting logical key width to %0.2f" % width)

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
        # TODO(miket): this turned out to be complicated to figure out exactly. So we
        self.update_bounding_box(x, y)

    def mark_switch_position(self, part):
        x, y = self.get_part_position()
        self.mark_component_position(part, 0, 0, 180, 'top')

    def mark_diode_position(self, part):
        x, y = self.get_part_position()
        x_offset, y_offset = (2, -self.__mx_key_width / 5)
        self.mark_component_position(part, x_offset, y_offset, 0, 'bottom')

    def mark_pro_micro_position(self, part):
        x, y = self.get_part_position()
        self.mark_component_position(part, 0, 0, 0, 'top')

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


class KeyCad:
    def __init__(self, pcb):
        self.__row_index = 0
        self.__col_index = 0
        self.__keysw_partno = 1
        self.__d_partno = 1
        self.__key_matrix_rows = []
        self.__key_matrix_cols = []

        self.__pcb = pcb

        self.__vcc = Net('VCC')
        self.__gnd = Net('GND')

    def process_row_metadata(self, metadata):
        print(metadata)

    def process_key_metadata(self, metadata):
        if 'w' in metadata:
            self.__pcb.set_logical_key_width(float(metadata['w']))

    def create_keyswitch(self, key):
        # keyboard_parts.lib is found at https://github.com/tmk/kicad_lib_tmk
        part = Part('keycad',
                    '~KEYSW',
                    NETLIST,
                    footprint='keycad:Kailh_socket_MX')
        part.ref = "K%d" % (self.__keysw_partno)
        part.value = "foo"  #str(key)
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

    def process_key(self, key):
        print("key at (%d %d): %s" % (self.__row_index, self.__col_index, key))

        part = self.create_keyswitch(key)
        part = self.create_diode()

        net = Net("%s_%s" % (part.ref, part.ref))
        net += part[2], part[2]
        self.__key_matrix_rows[self.__row_index] += part[1]
        self.__key_matrix_cols[self.__col_index] += part[2]

    def process_row(self, row):
        self.__col_index = 0
        self.__key_matrix_rows.append(Net("row%d" % self.__row_index))
        for key in row:
            if len(self.__key_matrix_cols) <= self.__col_index:
                self.__key_matrix_cols.append(Net("col%d" % self.__col_index))
            if isinstance(key, dict):
                self.process_key_metadata(key)
            else:
                self.process_key(key)
                self.__col_index += 1
                self.__pcb.advance_cursor()

    def handle_kle_json(self, json):
        for row in kle_json:
            if isinstance(row, dict):
                self.process_row_metadata(row)
            else:
                self.process_row(row)
                self.__row_index += 1
                print("next row")
                self.__pcb.cursor_carriage_return()

    def connect_pro_micro(self, pro_micro):
        pro_micro_next_pin = 5
        self.__gnd += pro_micro[3], pro_micro[4], pro_micro[23]
        self.__vcc += pro_micro[21]
        for row in self.__key_matrix_rows:
            row += pro_micro[pro_micro_next_pin]
            pro_micro_next_pin += 1
        for col in self.__key_matrix_cols:
            col += pro_micro[pro_micro_next_pin]
            pro_micro_next_pin += 1


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

# Output the netlist to a file.
generate_netlist()

# pour ground fills
# reset button
# LEDs
# underglow LEDs

f = open("keycad-kinjector.json", "w")
f.write(
    json.dumps({'board': {
        'modules': pcb.get_kinjector_dict()
    }},
               sort_keys=True,
               indent=4))
f.close()

(l, t, r, b) = pcb.get_bounding_box()
print("pcb bounding box: (%d %d), (%d %d)" % (l, t, r, b))