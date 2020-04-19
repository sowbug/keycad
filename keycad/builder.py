class BoardBuilder:
    def __init__(self, kle, schematic):
        self._kle = kle
        self._schematic = schematic

    def build(self,
              add_pro_micro=True,
              add_blue_pill=False,
              add_per_key_rgb=True):
        mcu = None
        if add_pro_micro:
            mcu = self._schematic.create_pro_micro()
        if add_blue_pill:
            mcu = self._schematic.create_blue_pill()

        self._schematic.create_matrix_nets(self._kle.key_count,
                                           self._kle.row_count,
                                           self._kle.max_col_count,
                                           mcu.gpio_count)
        board_width = self._kle.board_right - self._kle.board_left
        board_height = self._kle.board_bottom - self._kle.board_top
        led_identifier = 0
        for key in self._kle.keys:
            self._schematic.add_key(key)
            if add_per_key_rgb:
                self._schematic.add_per_key_rgb(key)
            (led_x, led_y) = key.position
            # https://docs.qmk.fm/#/feature_rgb_matrix
            key.led_x = (led_x / board_width) * 224
            key.led_y = (led_y / board_height) * 64
            key.led_identifier = led_identifier
            led_identifier += 1

        if add_pro_micro:
            reset = self._schematic.create_reset_switch()
            self._schematic.connect_reset_switch(reset, mcu)
        if add_blue_pill:
            pass
        if mcu:
            self._schematic.connect_mcu(mcu)

            if add_blue_pill:
                # TODO(miket): manual wiring option for Pro Micro
                conn = self._schematic.create_usb_c_connector()
                r1 = self._schematic.create_resistor("5K1")
                r2 = self._schematic.create_resistor("5K1")
                self._schematic.connect_usb_c_connector(conn, mcu, r1, r2)
