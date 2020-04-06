class BoardBuilder:
    def __init__(self, kle, schematic):
        self.__kle = kle
        self.__schematic = schematic

    def build(self, add_pro_micro=True, add_blue_pill=False):
        self.__schematic.create_matrix_nets()
        for key in self.__kle.keys:
            self.__schematic.add_key(key)

        mcu = None
        if add_pro_micro:
            mcu = self.__schematic.create_pro_micro()
            reset = self.__schematic.create_reset_switch()
            self.__schematic.connect_reset_switch(reset, mcu)
        if add_blue_pill:
            mcu = self.__schematic.create_blue_pill()
        if mcu:
            self.__schematic.connect_mcu(mcu)

            conn = self.__schematic.create_usb_c_connector()
            r1 = self.__schematic.create_resistor("5K1")
            r2 = self.__schematic.create_resistor("5K1")
            self.__schematic.connect_usb_c_connector(conn, mcu, r1, r2)
