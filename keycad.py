#!/usr/bin/env python3

import argparse
import json

from skidl import *

KC_TO_MM = 1000000


class KeyCad:
    def __init__(self):
        self.__kinjector_json = {}

        self.__row_index = 0
        self.__col_index = 0
        self.__keysw_partno = 1
        self.__diode_partno = 1
        self.__key_matrix_rows = []
        self.__key_matrix_cols = []

        self.__pcb_key_cursor_x = 0
        self.__pcb_key_cursor_y = 0

        self.__vcc = Net('VCC')
        self.__gnd = Net('GND')

        self.__mx_key_width = 19.05

        self.reset_key_attributes()

    def process_row_metadata(self, metadata):
        print(metadata)

    def process_key_metadata(self, metadata):
        if 'w' in metadata:
            self.__key_width = int(metadata['w'])

    def get_pcb_position_x(self):
        return int(
            (self.__pcb_key_cursor_x +
             ((self.__key_width - 1) * self.__mx_key_width / 2)) * KC_TO_MM)

    def get_pcb_position_y(self):
        return int(self.__pcb_key_cursor_y * KC_TO_MM)

    def get_diode_offset_x(self):
        return 2 * KC_TO_MM

    def get_diode_offset_y(self):
        return (-self.__mx_key_width / 5) * KC_TO_MM

    def create_keyswitch(self, key):
        keysw_part = Part('keyboard_parts',
                          '~KEYSW',
                          NETLIST,
                          footprint='daprice:Kailh_socket_MX')
        keysw_part.ref = "K%d" % (self.__keysw_partno)
        keysw_part.value = str(key)
        self.__keysw_partno += 1

        self.__kinjector_json[keysw_part.ref] = {
            'position': {
                'x': self.get_pcb_position_x(),
                'y': self.get_pcb_position_y(),
                'angle': 180,
                'side': 'top'
            }
        }

        return keysw_part

    def create_diode(self):
        diode_part = Part('Device',
                          'D',
                          NETLIST,
                          footprint='keeb:D_0805')
        diode_part.ref = "D%d" % (self.__diode_partno)
        diode_part.value = "1N4148"
        self.__diode_partno += 1

        self.__kinjector_json[diode_part.ref] = {
            'position': {
                'x': self.get_pcb_position_x() + self.get_diode_offset_x(),
                'y': self.get_pcb_position_y() + self.get_diode_offset_y(),
                'angle': 0,
                'side': 'bottom'
            }
        }
        return diode_part

    def advance_pcb_cursor(self, end_of_row=False):
        self.__pcb_key_cursor_x += self.__mx_key_width * self.__key_width
        if end_of_row:
            self.__pcb_key_cursor_x = 0
            self.__pcb_key_cursor_y += self.__mx_key_width

    def process_key(self, key):
        print("key at (%d %d): %s" % (self.__row_index, self.__col_index, key))

        keysw_part = self.create_keyswitch(key)
        diode_part = self.create_diode()

        net = Net("%s_%s" % (keysw_part.ref, diode_part.ref))
        net += keysw_part[2], diode_part[2]
        self.__key_matrix_rows[self.__row_index] += diode_part[1]
        self.__key_matrix_cols[self.__col_index] += diode_part[2]

    def reset_key_attributes(self):
        self.__key_width = 1

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
                self.__col_index += int(self.__key_width)
                self.advance_pcb_cursor(False)
                self.reset_key_attributes()

    def handle_kle_json(self, json):
        for row in kle_json:
            if isinstance(row, dict):
                self.process_row_metadata(row)
            else:
                self.process_row(row)
                self.__row_index += 1
                self.advance_pcb_cursor(True)

    def add_pro_micro(self):
        pro_micro = Part('keebio',
                         'ProMicro',
                         NETLIST,
                         footprint='keeb:ArduinoProMicro')
        pro_micro.ref = 'U1'
        pro_micro.value = 'Pro Micro'
        pro_micro_next_pin = 5
        self.__gnd += pro_micro[3], pro_micro[4], pro_micro[23]
        self.__vcc += pro_micro[21]
        for row in self.__key_matrix_rows:
            row += pro_micro[pro_micro_next_pin]
            pro_micro_next_pin += 1
        for col in self.__key_matrix_cols:
            col += pro_micro[pro_micro_next_pin]
            pro_micro_next_pin += 1

    def get_kinjector_dict(self):
        return self.__kinjector_json


parser = argparse.ArgumentParser(
    description=
    'Generate keyboard manufacturing files from www.keyboard-layout-editor.com JSON.'
)
parser.add_argument('kle_json_filename', help='KLE JSON filename')
args = parser.parse_args()

keycad = KeyCad()

json_text = open(args.kle_json_filename, "r").read()
kle_json = json.loads(json_text)
keycad.handle_kle_json(kle_json)

keycad.add_pro_micro()

# Output the netlist to a file.
generate_netlist()

# board outline
# pour ground fills
# reset button
# LEDs
# underglow LEDs

f = open("keycad-kinjector.json", "w")
f.write(json.dumps({'board': {'modules': keycad.get_kinjector_dict()}}))
f.close()