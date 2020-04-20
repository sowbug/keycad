import sys

from skidl import Net

from keycad import key
from keycad import mcu
from keycad import partstore


class Schematic:
    def __init__(self, store, pcb, is_mx=True, is_hotswap=True):
        self._partstore = store
        self.__key_matrix_rows = []
        self.__key_matrix_cols = []
        self.__key_matrix_keys = None

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

        self.__led_din_pin_name = None

    @property
    def key_matrix_keys(self):
        return self.__key_matrix_keys

    @property
    def led_data_pin_name(self):
        return self.__led_din_pin_name

    def create_keyswitch(self, key):
        part = self._partstore.get_keyswitch(key.printable_label, self._is_mx,
                                             self._is_hotswap)
        self.__pcb.place_keyswitch_on_keyboard_grid(part, key)
        return part

    def create_key_rgb(self, key):
        part = self._partstore.get_per_key_rgb_led()
        self.__pcb.place_led_on_keyboard_grid(part, key)
        return part

    def create_key_rgb_capacitor(self, key):
        part = self._partstore.get_capacitor("0.1uF")
        self.__pcb.place_led_capacitor_on_keyboard_grid(part, key)
        return part

    def connect_per_key_rgb(self, led):
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

    def connect_per_key_rgb_capacitor(self, c):
        self.__vcc += c[1]
        self.__gnd += c[2]

    def create_diode(self, key):
        part = self._partstore.get_diode()
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

    def assign_matrix_location_to_key(self, key):
        key.matrix_col = self.__key_matrix_x
        key.matrix_row = self.__key_matrix_y
        self.__key_matrix_keys[self.__key_matrix_y][self.__key_matrix_x] = key

    def connect_keyswitch_and_diode(self, key, keysw_part, diode_part):
        net = Net("%s_%s" % (keysw_part.ref, diode_part.ref))
        net += keysw_part[2], diode_part[2]

        # COL2ROW means the connection goes COL_ to switch to diode anode
        # to diode cathode to ROW_. See
        # https://github.com/qmk/qmk_firmware/blob/master/docs/config_options.md
        self.assign_matrix_location_to_key(key)
        self.connect_to_matrix(keysw_part[1], diode_part[1])

    def add_key(self, key, add_led=True):
        if key.y != self._prior_y:
            if self._prior_y != -1:
                self.advance_matrix_row()
            self._prior_y = key.y

        keysw_part = self.create_keyswitch(key)
        d_part = self.create_diode(key)
        self.connect_keyswitch_and_diode(key, keysw_part, d_part)

    def add_per_key_rgb(self, key):
        led_part = self.create_key_rgb(key)
        cap_part = self.create_key_rgb_capacitor(key)
        self.connect_per_key_rgb(led_part)
        self.connect_per_key_rgb_capacitor(cap_part)

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
        self.__key_matrix_keys = [[None] * col_count for i in range(row_count)]

    def connect_mcu(self, mcu):
        self.__gnd += mcu.get_gnd_pins()
        self.__vcc += mcu.get_vcc_pins()

        if self.__led_din_pin is not None:
            self.__led_din_pin += mcu.claim_led_din_pin()
            self.__led_din_pin.net.name = "LED_DATA"
            self.__led_din_pin_name = mcu.get_pin_name(mcu.led_din_pin_no)

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
        uc = mcu.ProMicro(self._partstore)
        uc.place(self.__pcb)
        return uc

    def create_blue_pill(self):
        uc = mcu.BluePill(self._partstore)
        uc.place(self.__pcb)
        return uc

    def create_reset_switch(self):
        part = self._partstore.get_reset_switch()
        self.__pcb.place_reset_switch_on_keyboard_grid(part)
        return part

    def create_usb_c_connector(self):
        part = self._partstore.get_usb_c_connector()
        self.__pcb.place_usb_c_connector_on_keyboard_grid(part)
        return part

    def create_resistor(self, value):
        part = self._partstore.get_resistor(value)
        self.__pcb.place_resistor_on_keyboard_grid(part)
        return part

    def get_legend_dict(self):
        return {"cols": self.__legend_cols, "rows": self.__legend_rows}

    def get_legend_text(self):
        return "Rows: %s Cols: %s" % ("/".join(self.__legend_rows), "/".join(
            self.__legend_cols))
