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
        if add_blue_pill:
            mcu = self.__schematic.create_blue_pill()
        if mcu:
            self.__schematic.connect_mcu(mcu)
            reset = self.__schematic.create_reset_switch()
            self.__schematic.connect_reset_switch(reset, mcu)
            if True:
                conn = self.__schematic.create_usb_c_connector()
                self.__schematic.connect_usb_c_connector(conn, mcu)
