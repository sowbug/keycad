from keycad import partstore


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
    def __init__(self, store):
        super().__init__()
        self._part = store.get_mcu(partstore.McuType.ProMicro)
        self._part.ref = 'U1'
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
    def __init__(self, store):
        super().__init__()
        self._part = store.get_mcu(partstore.McuType.BluePill)
        self._part.ref = 'U2'
        self.gpio_pin_nos = [
            3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 21, 22, 23, 24,
            25, 26, 27, 30, 31, 32, 33, 34, 35, 36, 37
        ]
        self.pin_names = [
            # 1-8
            "VBAT",
            "LED1",  # C13
            "C14",
            "C15",
            "A0",
            "A1",
            "A2",
            "A3",

            # 9-16
            "A4",
            "A5",
            "A6",
            "A7",
            "B0",
            "B1",
            "B10",
            "B11",

            # 17-24
            "RST",
            "3V3",
            "GND",
            "GND",
            "B12",
            "B13",
            "B14",
            "B15",

            # 25-32
            "A8",
            "A9",
            "A10",
            "USB_DM",  # A11
            "USB_DP",  # A12
            "A15",
            "B3",
            "B4",

            # 33-40
            "B5",
            "B6",
            "B7",
            "B8",
            "B9",
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
