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


class Mcu:
    def __init__(self):
        self._part = []
        self._next_pin_index = 0
        self.gpio_pins = []
        self.vcc_pins = []
        self.gnd_pins = []
        self.led_din_pin = -1
        self.reset_pin = -1

    def get_gnd_pins(self):
        pins = []
        for n in self.gnd_pins:
            pins.append(self._part[n])
        return tuple(pins)

    def get_vcc_pins(self):
        pins = []
        for n in self.vcc_pins:
            pins.append(self._part[n])
        return tuple(pins)

    def gpio_count(self):
        return len(self.gpio_pins)

    def claim_next_gpio(self):
        if len(self.gpio_pins) == 0:
            raise RuntimeError("Ran out of GPIOs")
        val = self.gpio_pins.pop(0)
        return (val, self._part[val])

    def get_led_din_pin(self):
        self.gpio_pins.remove(self.led_din_pin)
        return self._part[self.led_din_pin]

    def get_reset_pin(self):
        return self._part[self.reset_pin]


class ProMicro(Mcu):
    GPIOS = [1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    PIN_NAMES = [
        "D3", "D2", "GND", "GND", "D1", "D0", "D4", "C6", "D7", "E6", "B4",
        "B5", "B6", "B2", "B3", "B1", "F7", "F6", "F5", "F4", "VCC", "RST",
        "GND", "RAW"
    ]

    VCC_PINS = [21]
    GND_PINS = [3, 4, 23]
    LED_DIN_PIN = 5
    RESET_PIN = 22

    def __init__(self):
        super().__init__()
        self._part = Part('keycad',
                          'ProMicro',
                          NETLIST,
                          footprint='keycad:ArduinoProMicro')
        self._part.ref = 'U1'
        self._part.value = 'Pro Micro'
        self.gpio_pins = ProMicro.GPIOS.copy()
        self.gnd_pins = ProMicro.GND_PINS
        self.vcc_pins = ProMicro.VCC_PINS
        self.led_din_pin = ProMicro.LED_DIN_PIN
        self.reset_pin = ProMicro.RESET_PIN

    def place(self, pcb):
        pcb.place_pro_micro_on_keyboard_grid(self._part)

    def get_pin_name(self, pin_number):
        return ProMicro.PIN_NAMES[pin_number - 1]


class BluePill(Mcu):
    def __init__(self):
        super().__init__(self)
        self._part = Part('keycad',
                          'ProMicro',
                          NETLIST,
                          footprint='keycad:ArduinoProMicro')
        self._part.ref = 'U2'
        self._part.value = 'Blue Pill'

    def place(self, pcb):
        pcb.place_blue_pill_on_keyboard_grid(self._part)


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
        # SK6812 Mini-E
        # 1 VCC
        # 2 DOUT
        # 3 GND
        # 4 DIN

        self.__vcc += led[1]
        self.__gnd += led[3]

        if self.__led_din_pin is None:
            self.__led_din_pin = led[4]
        if self.__led_dout_pin is None:
            self.__led_dout_pin = led[2]
        else:
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

    def connect_mcu(self, mcu):
        self.__gnd += mcu.get_gnd_pins()
        self.__vcc += mcu.get_vcc_pins()

        # TODO(miket): change to a method that allows asking for the
        # next GPIO, and then this can be refactored away
        if self.__led_din_pin is not None:
            self.__led_din_pin += mcu.get_led_din_pin()
            self.__led_din_pin.net.name = "LED_DATA"

        for row in self.__key_matrix_rows:
            if len(row) == 0:
                self.__key_matrix_rows.remove(row)
        for col in self.__key_matrix_cols:
            if len(col) == 0:
                self.__key_matrix_cols.remove(col)

        if False and len(self.__key_matrix_rows) + len(
                self.__key_matrix_cols) > mcu.gpio_count():
            print(
                "ERROR: need pins to connect %d rows and %d cols but have only %d GPIOs"
                % (len(self.__key_matrix_rows), len(
                    self.__key_matrix_cols), mcu.gpio_count()))
            sys.exit(1)
        for row in self.__key_matrix_rows:
            pin_no, pin_net = mcu.claim_next_gpio()
            self.__legend_rows.append(mcu.get_pin_name(pin_no))
            row += pin_net
        for col in self.__key_matrix_cols:
            pin_no, pin_net = mcu.claim_next_gpio()
            self.__legend_cols.append(mcu.get_pin_name(pin_no))
            col += pin_net

    def connect_reset_switch(self, reset, mcu):
        self.__gnd += reset[2]
        reset[1] += mcu.get_reset_pin()
        reset[1].net.name = "RST"

    def set_next_dout_pin(self, next_dout_pin):
        self.__next_dout_pin = next_dout_pin

    def create_pro_micro(self):
        mcu = ProMicro()
        mcu.place(self.__pcb)
        return mcu

    def create_blue_pill(self):
        mcu = BluePill()
        mcu.place(self.__pcb)
        return mcu

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
        return "ROWS: %s\nCOLS: %s" % (" ".join(self.__legend_rows), " ".join(
            self.__legend_cols))
