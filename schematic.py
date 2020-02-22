from skidl import Part, Net, NETLIST

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
    "Caps Lock": 'CAPS',
    "Shift": 'SHFT',
    "Backspace": "BSPC",
    "Enter": "ENT"
}


class KeyCad:
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
            self.__key_matrix_rows.append(Net("ROW_%d" % y))
        for x in range(0, 9):
            self.__key_matrix_cols.append(Net("COL_%d" % x))

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
            row += pro_micro[PRO_MICRO_GPIOS[next_pin_index]]
            next_pin_index += 1
        for col in self.__key_matrix_cols:
            col += pro_micro[PRO_MICRO_GPIOS[next_pin_index]]
            next_pin_index += 1

    def connect_reset_switch(self, reset, pro_micro):
        self.__gnd += reset[2]
        pro_micro[22] += reset[1]
        reset[1].net.name = "RST"

    def set_next_dout_pin(self, next_dout_pin):
        self.__next_dout_pin = next_dout_pin

    def create_pro_micro(self):
        pro_micro = Part('keycad',
                         'ProMicro',
                         NETLIST,
                         footprint='keycad:ArduinoProMicro')
        pro_micro.ref = 'U1'
        pro_micro.value = 'Pro Micro'
        return pro_micro

    def create_reset_switch(self):
        reset = Part('keycad',
                     'SW_Push',
                     NETLIST,
                     footprint='keycad:SW_SPST_SKQG_WithoutStem')
        reset.ref = 'SW1'
        reset.value = 'SKQGAKE010'
        return reset
