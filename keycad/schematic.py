import sys

from skidl import NETLIST, Net, Part

from keycad import key

# KiCad explodes with raw quote
# freerouting.jar explodes with raw backtick
SYMBOL_TO_ALNUM = {
    "'": 'QUOT',
    "`": 'GRV',
    "↑": 'UP',
    "↓": 'DOWN',
    "←": 'LEFT',
    "→": 'RGHT',
    "": 'SPC',
    "|": 'BAR',
    "!": 'EXCL',
    "@": 'AT',
    "#": 'HASH',
    "$": 'DLR',
    "%": 'PCT',
    "^": 'CRT',
    "&": 'AMP',
    "*": 'AST',
    "(": 'LPRN',
    ")": 'RPRN',
    "-": 'DASH',
    "=": 'EQU',
    "Caps Lock": 'CAPS',
    "Shift": 'SHFT',
    "Backspace": "BSPC",
    "Enter": "ENT"
}


class Schematic:
    def __init__(self, pcb):
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

        self.__legend_rows = []
        self.__legend_cols = []

    def get_key_value(self, key_labels):
        if len(key_labels) > 1:
            label = key_labels[1]
        else:
            label = key_labels[0]
        if label in SYMBOL_TO_ALNUM:
            return SYMBOL_TO_ALNUM[label]
        return label

    def create_keyswitch(self, key):
        # keyboard_parts.lib is found at https://github.com/tmk/kicad_lib_tmk
        part = Part('keycad',
                    'KEYSW',
                    NETLIST,
                    footprint='keycad:Kailh_socket_MX')
        part.ref = "K%d" % (self.__keysw_partno)
        part.value = self.get_key_value(key.labels)
        self.__keysw_partno += 1
        self.__pcb.place_keyswitch_on_keyboard_grid(part, key)
        return part

    def create_key_led(self, key):
        part = Part('keycad',
                    'SK6812MINI-E',
                    NETLIST,
                    footprint='keycad:SK6812-MINI-E-BOTTOM')
        part.ref = "LED%d" % (self.__led_partno)
        part.value = "SK6812MINI-E"
        self.__led_partno += 1
        self.__pcb.place_led_on_keyboard_grid(part, key)
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

    def create_diode(self, key):
        part = Part('keycad', 'D', NETLIST, footprint='keycad:D_0805')
        part.ref = "D%d" % (self.__d_partno)
        part.value = "1N4148"
        self.__d_partno += 1
        self.__pcb.place_diode_on_keyboard_grid(part, key)
        return part

    def connect_to_matrix(self, pin_1, pin_2):
        self.__key_matrix_rows[self.__key_matrix_x] += pin_1
        self.__key_matrix_cols[self.__key_matrix_y] += pin_2

        # TODO(miket): for now we naively assume that keys are connected
        # left to right, top to bottom. Eventually we should replace this
        # with something that fits the actual board layout.
        self.__key_matrix_x += 1
        if self.__key_matrix_x >= len(self.__key_matrix_cols):
            self.__key_matrix_x = 0
            self.__key_matrix_y += 1

    def connect_keyswitch_and_diode(self, key, keysw_part, diode_part):
        net = Net("%s_%s" % (keysw_part.ref, diode_part.ref))
        net += keysw_part[2], diode_part[2]
        self.connect_to_matrix(diode_part[1], keysw_part[1])

    def add_key(self, key):
        keysw_part = self.create_keyswitch(key)
        d_part = self.create_diode(key)
        self.connect_keyswitch_and_diode(key, keysw_part, d_part)

        led_part = self.create_key_led(key)
        self.connect_per_key_led(led_part)

    def create_matrix_nets(self):
        # TODO(miket): calculate right number
        for y in range(0, 9):
            self.__key_matrix_rows.append(Net("ROW_%d" % y))
        for x in range(0, 9):
            self.__key_matrix_cols.append(Net("COL_%d" % x))

    def connect_pro_micro(self, pro_micro):
        # Python 3.7 and later:
        #
        # https://mail.python.org/pipermail/python-dev/2017-December/151283.html
        # Make it so. "Dict keeps insertion order" is the ruling.
        #
        # This matters because we want everyone running the same code/KLE
        # to generate the same board.
        PRO_MICRO_GPIOS = [{
            "name": "D3",
            "pin": 1
        }, {
            "name": "D2",
            "pin": 2
        }, {
            "name": "D1",
            "pin": 5,
            "supports_led": True
        }, {
            "name": "D0",
            "pin": 6
        }, {
            "name": "D4",
            "pin": 7
        }, {
            "name": "C6",
            "pin": 8
        }, {
            "name": "D7",
            "pin": 9
        }, {
            "name": "E6",
            "pin": 10
        }, {
            "name": "B4",
            "pin": 11
        }, {
            "name": "B5",
            "pin": 12
        }, {
            "name": "B6",
            "pin": 13
        }, {
            "name": "B2",
            "pin": 14
        }, {
            "name": "B3",
            "pin": 15
        }, {
            "name": "B1",
            "pin": 16
        }, {
            "name": "F7",
            "pin": 17
        }, {
            "name": "F6",
            "pin": 18
        }, {
            "name": "F5",
            "pin": 19
        }, {
            "name": "F4",
            "pin": 20
        }]

        next_pin_index = 0
        self.__gnd += pro_micro[3], pro_micro[4], pro_micro[23]
        self.__vcc += pro_micro[21]

        # TODO(miket): change to a method that allows asking for the
        # next GPIO, and then this can be refactored away
        if self.__led_din_pin is not None:
            led_pin = None
            for p in PRO_MICRO_GPIOS:
                if "supports_led" in p and p["supports_led"]:
                    PRO_MICRO_GPIOS.remove(p)
                    led_pin = p
            pro_micro[led_pin["pin"]] += self.__led_din_pin

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
            p = PRO_MICRO_GPIOS[next_pin_index]
            row += pro_micro[p["pin"]]
            self.__legend_rows.append(p["name"])
            next_pin_index += 1
        for col in self.__key_matrix_cols:
            p = PRO_MICRO_GPIOS[next_pin_index]
            col += pro_micro[p["pin"]]
            self.__legend_cols.append(p["name"])
            next_pin_index += 1

    def connect_reset_switch(self, reset, pro_micro):
        self.__gnd += reset[2]
        pro_micro[22] += reset[1]
        reset[1].net.name = "RST"

    def set_next_dout_pin(self, next_dout_pin):
        self.__next_dout_pin = next_dout_pin

    def create_pro_micro(self):
        part = Part('keycad',
                    'ProMicro',
                    NETLIST,
                    footprint='keycad:ArduinoProMicro')
        part.ref = 'U1'
        part.value = 'Pro Micro'
        self.__pcb.place_pro_micro_on_keyboard_grid(part)
        return part

    def create_reset_switch(self):
        part = Part('keycad',
                    'SW_Push',
                    NETLIST,
                    footprint='keycad:SW_SPST_SKQG_WithoutStem')
        part.ref = 'SW1'
        part.value = 'SKQGAKE010'
        self.__pcb.place_reset_switch_on_keyboard_grid(part)
        return part

    def get_legend(self):
        return "ROWS: %s\nCOLS: %s" % (" ".join(self.__legend_rows),
                                       " ".join(self.__legend_cols))
