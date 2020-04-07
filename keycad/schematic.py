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
        self.gpio_pin_nos = []
        self.pin_names = []
        self.vcc_pin_nos = []
        self.gnd_pin_nos = []
        self.led_din_pin_no = -1
        self.reset_pin_no = -1
        self.usb_pin_nos = (-1, -1)

    @property
    def pin_count(self):
        return len(self.pin_names)

    def get_pin_name(self, pin_no):
        return self.pin_names[pin_no - 1]

    def populate_pins(self, pin_names):
        for pin_no in range(1, self.pin_count):
            name = self.get_pin_name(pin_no)
            if name == "GND":
                self.gnd_pin_nos.append(pin_no)
            if name == "VCC":
                self.vcc_pin_nos.append(pin_no)
            if name == "RST":
                self.reset_pin_no = pin_no

    def get_gnd_pins(self):
        pins = []
        for no in self.gnd_pin_nos:
            pins.append(self._part[no])
        return tuple(pins)

    def get_vcc_pins(self):
        pin_nos = []
        for no in self.vcc_pin_nos:
            pin_nos.append(self._part[no])
        return tuple(pin_nos)

    @property
    def gpio_count(self):
        return len(self.gpio_pin_nos)

    def claim_next_gpio(self):
        if len(self.gpio_pin_nos) == 0:
            raise RuntimeError("Ran out of GPIOs")
        val = self.gpio_pin_nos.pop(0)
        return (val, self._part[val])

    def claim_led_din_pin(self):
        if self.led_din_pin_no in self.gpio_pin_nos:
            self.gpio_pin_nos.remove(self.led_din_pin_no)
        return self._part[self.led_din_pin_no]

    def get_reset_pin_no(self):
        return self.reset_pin_no

    def get_reset_pin(self):
        return self._part[self.get_reset_pin_no()]

    def get_usb_pin_nos(self):
        return self.usb_pin_nos

    def get_usb_pins(self):
        dp_pin_no, dm_pin_no = self.get_usb_pin_nos()
        return self._part[dp_pin_no], self._part[dm_pin_no]


class ProMicro(Mcu):
    def __init__(self):
        super().__init__()
        self._part = Part('keycad',
                          'ProMicro',
                          NETLIST,
                          footprint='keycad:ArduinoProMicro')
        self._part.ref = 'U1'
        self._part.value = 'Pro Micro'
        self.gpio_pin_nos = [
            1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
        ]
        self.pin_names = [
            "D3", "D2", "GND", "GND", "D1", "D0", "D4", "C6", "D7", "E6", "B4",
            "B5", "B6", "B2", "B3", "B1", "F7", "F6", "F5", "F4", "VCC", "RST",
            "GND", "RAW"
        ]
        self.populate_pins(self.pin_names)
        self.led_din_pin_no = 5

    def place(self, pcb):
        pcb.place_pro_micro_on_keyboard_grid(self._part)


class BluePill(Mcu):
    def __init__(self):
        super().__init__()
        self._part = Part('keycad',
                          'BluePill_STM32F103C',
                          NETLIST,
                          footprint='keycad:BluePill_STM32F103C')
        self._part.ref = 'U2'
        self._part.value = 'Blue Pill'
        self.gpio_pin_nos = [
            3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 21, 22, 23, 24,
            25, 26, 27, 30, 31, 32, 33, 34, 35, 36, 37
        ]
        self.pin_names = [
            # 1-8
            "VBAT",
            "LED1",  # PC_13
            "PC_14",
            "PC_15",
            "PA_0",
            "PA_1",
            "PA_2",
            "PA_3",

            # 9-16
            "PA_4",
            "PA_5",
            "PA_6",
            "PA_7",
            "PB_0",
            "PB_1",
            "PB_10",
            "PB_11",

            # 17-24
            "RST",
            "3V3",
            "GND",
            "GND",
            "PB_12",
            "PB_13",
            "PB_14",
            "PB_15",

            # 25-32
            "PA_8",
            "PA_9",
            "PA_10",
            "USB_DM",  # PA_11
            "USB_DP",  # PA_12
            "PA_15",
            "PB_3",
            "PB_4",

            # 33-40
            "PB_5",
            "PB_6",
            "PB_7",
            "PB_8",
            "PB_9",
            "VCC",
            "GND",
            "3V3"
        ]

        self.populate_pins(self.pin_names)

        # TODO(miket): check which pin other STM32-based boards use
        self.led_din_pin_no = 37

        self.usb_pin_nos = (29, 28)

    def place(self, pcb):
        pcb.place_blue_pill_on_keyboard_grid(self._part)


class Schematic:
    def __init__(self, pcb, is_mx=True, is_hotswap=True):
        self.__keysw_partno = 1
        self.__d_partno = 1
        self.__r_partno = 1
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

        self._is_mx = is_mx
        self._is_hotswap = is_hotswap

        self._prior_y = -1

    def get_key_value(self, key_labels):
        if len(key_labels) > 1:
            label = key_labels[1]
        else:
            label = key_labels[0]
        if label in SYMBOL_TO_ALNUM:
            return SYMBOL_TO_ALNUM[label]
        return label

    def create_keyswitch(self, key):
        if self._is_mx:
            switch_type = "MX"
        else:
            switch_type = "PG1350"
        if self._is_hotswap:
            socket_type = "Kailh_socket"
        else:
            socket_type = "SW"
        footprint = "keycad:%s_%s" % (socket_type, switch_type)
        part = Part('keycad', 'KEYSW', NETLIST, footprint=footprint)
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
        self.__key_matrix_cols[self.__key_matrix_x] += pin_1
        self.__key_matrix_rows[self.__key_matrix_y] += pin_2
        self.__key_matrix_x += 1

    def advance_matrix_row(self):
        if self._conserve_cols:
            return
        self.__key_matrix_x = 0
        self.__key_matrix_y += 1

    def connect_keyswitch_and_diode(self, key, keysw_part, diode_part):
        net = Net("%s_%s" % (keysw_part.ref, diode_part.ref))
        net += keysw_part[2], diode_part[2]

        # COL2ROW means the connection goes COL_ to switch to diode anode
        # to diode cathode to ROW_. See
        # https://github.com/qmk/qmk_firmware/blob/master/docs/config_options.md
        self.connect_to_matrix(keysw_part[1], diode_part[1])

    def add_key(self, key):
        if key.y != self._prior_y:
            if self._prior_y != -1:
                self.advance_matrix_row()
            self._prior_y = key.y

        keysw_part = self.create_keyswitch(key)
        d_part = self.create_diode(key)
        self.connect_keyswitch_and_diode(key, keysw_part, d_part)

        led_part = self.create_key_led(key)
        self.connect_per_key_led(led_part)

    def create_matrix_nets(self, key_count, key_row_count, key_col_count,
                           gpio_count):
        if key_row_count + key_col_count <= gpio_count:
            row_count = key_row_count
            col_count = key_col_count
            self._conserve_cols = False
        else:
            import math
            square_matrix_size = math.ceil(math.sqrt(key_count))
            if square_matrix_size * 2 >= gpio_count:
                raise OverflowError("not enough GPIOs for this keyboard")
            row_count = square_matrix_size
            col_count = square_matrix_size
            self._conserve_cols = True
        for y in range(0, row_count):
            self.__key_matrix_rows.append(Net("ROW_%d" % (y + 1)))
        for x in range(0, col_count):
            self.__key_matrix_cols.append(Net("COL_%d" % (x + 1)))

    def connect_mcu(self, mcu):
        self.__gnd += mcu.get_gnd_pins()
        self.__vcc += mcu.get_vcc_pins()

        if self.__led_din_pin is not None:
            self.__led_din_pin += mcu.claim_led_din_pin()
            self.__led_din_pin.net.name = "LED_DATA"

        for row in self.__key_matrix_rows:
            if len(row) == 0:
                self.__key_matrix_rows.remove(row)
        for col in self.__key_matrix_cols:
            if len(col) == 0:
                self.__key_matrix_cols.remove(col)

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

    def connect_usb_c_connector(self, conn, mcu, r1, r2):
        self.__gnd += conn["A1"], conn["A12"], conn["B1"], conn["B12"]
        self.__vcc += conn["A4"], conn["A9"], conn["B4"], conn["B9"]

        # TODO(miket): Per ST AN4775, 22-ohm resistors aren't necessary.
        usb_dp, usb_dm = mcu.get_usb_pins()
        conn["A6"] += conn["B6"]
        conn["A6"] += usb_dp
        conn["A6"].net.name = "USB_DP"
        conn["A7"] += conn["B7"]
        conn["A7"] += usb_dm
        conn["A7"].net.name = "USB_DM"

        # CC1 and CC2
        conn["A5"] += r1[1]
        conn["A5"].net.name = "CC1"
        r1[2] += self.__gnd
        conn["B5"] += r2[1]
        conn["B5"].net.name = "CC2"
        r2[2] += self.__gnd

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

    def create_usb_c_connector(self):
        part = Part('keycad',
                    'USB_C_Receptacle_USB2.0',
                    NETLIST,
                    footprint='keycad:USB_C_Receptacle_HRO_TYPE-C-31-M-14')
        part.ref = 'J1'
        part.value = 'TYPE-C-31-M-14'
        self.__pcb.place_usb_c_connector_on_keyboard_grid(part)
        return part

    def create_resistor(self, value):
        part = Part('keycad',
                    'R',
                    NETLIST,
                    footprint='keycad:R_0805_2012Metric')
        part.ref = "R%d" % (self.__r_partno)
        part.value = value
        self.__r_partno += 1
        self.__pcb.place_resistor_on_keyboard_grid(part)
        return part

    def get_legend_dict(self):
        return {"cols": self.__legend_cols, "rows": self.__legend_rows}
