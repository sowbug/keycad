import unittest
from keycad import schematic


class TestSchematic(unittest.TestCase):
    def check_mcu(self, mcu):

        # Are power pins named properly and excluded from GPIOs?
        for pin in mcu.gnd_pin_nos:
            self.assertEqual(mcu.get_pin_name(pin), "GND")
            self.assertFalse(pin in mcu.gpio_pin_nos)
        for pin in mcu.vcc_pin_nos:
            self.assertEqual(mcu.get_pin_name(pin), "VCC")
            self.assertFalse(pin in mcu.gpio_pin_nos)

        # Is reset pin named properly and excluded from GPIOs?
        self.assertEqual(mcu.get_pin_name(mcu.get_reset_pin_no()), "RST")
        self.assertFalse(mcu.get_reset_pin_no() in mcu.gpio_pin_nos)

        # Is LED DIN pin available until claimed?
        self.assertTrue(mcu.led_din_pin_no in mcu.gpio_pin_nos)
        mcu.claim_led_din_pin()
        self.assertFalse(mcu.led_din_pin_no in mcu.gpio_pin_nos)

    def test_pro_micro_pins(self):
        mcu = schematic.ProMicro()
        self.check_mcu(mcu)

    def test_blue_pill_pins(self):
        mcu = schematic.BluePill()
        self.check_mcu(mcu)
