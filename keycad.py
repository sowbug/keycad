#!/usr/bin/env python3

import argparse
import json

from skidl import *

kinjector_json = {}

row_index = 0
col_index = 0
keysw_partno = 1
diode_partno = 1
parts = []
key_matrix_rows = []
key_matrix_cols = []


def process_row_metadata(metadata):
    print(metadata)


def process_key_metadata(metadata):
    global col_index
    if 'w' in metadata:
        width = int(metadata['w'])
        print("key width is %d" % width)
        col_index += width - 1


def process_key(key):
    global row_index, col_index
    global key_matrix_rows, key_matrix_cols
    global keysw_partno, diode_partno
    print("key at (%d %d): %s" % (row_index, col_index, key))
    keysw_part = Part('keyboard_parts',
                      '~KEYSW',
                      NETLIST,
                      footprint='daprice:Kailh_socket_MX')
    keysw_part.ref = "K%d" % (keysw_partno)
    keysw_part.value = str(key)
    keysw_partno += 1
    parts.append(keysw_part)

    diode_part = Part('Device',
                      'D',
                      NETLIST,
                      footprint='keeb:Diode-Hybrid-Back')
    diode_part.ref = "D%d" % (diode_partno)
    diode_part.value = "1N4148"
    diode_partno += 1
    parts.append(diode_part)

    net = Net("%s_%s" % (keysw_part.ref, diode_part.ref))
    net += keysw_part[2], diode_part[2]
    key_matrix_rows[row_index] += diode_part[1]
    key_matrix_cols[col_index] += diode_part[2]

    global kinjector_json
    KC_TO_MM = 1000000
    kinjector_json[keysw_part.ref] = {
        'position': {
            'x': int(col_index * KC_TO_MM * 19.05),
            'y': int(row_index * KC_TO_MM * 19.05),
            'angle': 0,
            'side': 'top'
        }
    }
    kinjector_json[diode_part.ref] = {
        'position': {
            'x': int(col_index * KC_TO_MM * 19.05 + KC_TO_MM * 2),
            'y': int(row_index * KC_TO_MM * 19.05 + KC_TO_MM * 2),
            'angle': 90,
            'side': 'top'
        }
    }


def process_row(row):
    global row_index, col_index
    global key_matrix_rows, key_matrix_cols
    col_index = 0
    key_matrix_rows.append(Net("row%d" % row_index))
    for key in row:
        if len(key_matrix_cols) <= col_index:
            key_matrix_cols.append(Net("col%d" % col_index))
        if isinstance(key, dict):
            process_key_metadata(key)
        else:
            process_key(key)
            col_index += 1


parser = argparse.ArgumentParser(
    description=
    'Generate keyboard manufacturing files from www.keyboard-layout-editor.com JSON.'
)
parser.add_argument('kle_json_filename', help='KLE JSON filename')
args = parser.parse_args()

# Create input & output voltages and ground reference.
vin, vout, gnd = Net('VI'), Net('VO'), Net('GND')

pro_micro = Part('keebio',
                 'ProMicro',
                 NETLIST,
                 footprint='keeb:ArduinoProMicro')
pro_micro.ref = 'U1'
pro_micro.value = 'Pro Micro'

json_text = open(args.kle_json_filename, "r").read()
kle_json = json.loads(json_text)
for row in kle_json:
    if isinstance(row, dict):
        process_row_metadata(row)
    else:
        process_row(row)
        row_index += 1

pro_micro_next_pin = 5
for row in key_matrix_rows:
    row += pro_micro[pro_micro_next_pin]
    pro_micro_next_pin += 1
for col in key_matrix_cols:
    col += pro_micro[pro_micro_next_pin]
    pro_micro_next_pin += 1

# Output the netlist to a file.
generate_netlist()

f = open("keycad-kinjector.json", "w")
f.write(json.dumps({'board': {'modules': kinjector_json}}))
f.close()