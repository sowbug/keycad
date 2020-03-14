class BoardBuilder:
    def __init__(self, kle, schematic, pcb):
        self.__kle = kle
        self.__schematic = schematic
        self.__pcb = pcb

    def build(self):
        self.__schematic.create_matrix_nets()
        for key in self.__kle.keys:
            self.__schematic.add_key(key)

        pro_micro = self.__schematic.create_pro_micro()
        self.__schematic.connect_pro_micro(pro_micro)
        reset = self.__schematic.create_reset_switch()
        self.__schematic.connect_reset_switch(reset, pro_micro)
