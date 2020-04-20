import skidl
from enum import Enum


class _Part(Enum):
    BluePill = ("STM32 Development Board 'Blue Pill'", )
    ProMicro = ("Arduino Pro Micro", )
    MxSw = ("Cherry MX-compatible Switch", )
    MxKailh = ("Kailh MX-compatible Hotswap Socket", )
    Pg1350Sw = ("Kailh Choc-compatible Switch", )
    Pg1350Kailh = ("Kailh Choc Hotswap Socket", )
    Sk6812MiniE = ("SK6812 MINI-E RGB LED", )
    C0UF1 = ("0805 0.1uF Capacitor", )
    D1N4148 = ("0805 1N4148 Diode", )
    R5K1 = ("0805 5.1k Resistor", )
    SWSKQG = ("Alps SPST SKQG SMT Switch", )
    USB_HRO_C31M14 = ("Korean Hroparts TYPE-C-31-M-14 USB-C Connector", )


class McuType(Enum):
    ProMicro = 0
    BluePill = 1


class _RefType(Enum):
    IC = 0
    Diode = 1
    Capacitor = 2
    Resistor = 3
    LED = 4
    Keyswitch = 5
    Switch = 6
    Connector = 7


class PartStore:
    def __init__(self):
        self._parts = {}

        self._partno = [1, 1, 1, 1, 1, 1, 1, 1]

    @property
    def parts(self):
        return self._parts

    def get_bom(self):
        bom = []
        print(self.parts)
        for k, v in self.parts.items():
            d = _Part[k].value
            bom.append({"partno": k, "description": d[0], "quantity": v})
        return bom

    def assign_ref(self, ref_type):
        PREFIXES = {
            _RefType.IC: "U",
            _RefType.Diode: "D",
            _RefType.Capacitor: "C",
            _RefType.Resistor: "R",
            _RefType.LED: "L",
            _RefType.Keyswitch: "K",
            _RefType.Switch: "SW",
            _RefType.Connector: "J"
        }

        if not isinstance(ref_type, _RefType):
            raise ValueError("%s is not a _RefType enum" % (ref_type.value))

        val = "%s%d" % (PREFIXES[ref_type], self._partno[ref_type.value])
        self._partno[ref_type.value] += 1
        return val

    def record_part(self, part_key):
        if not isinstance(part_key, _Part):
            raise ValueError("%s is not a _Part enum" % (part_key))
        name = part_key.name
        if name in self._parts:
            self._parts[name] += 1
        else:
            self._parts[name] = 1

    def get_mcu(self, mcu_type):
        if not isinstance(mcu_type, McuType):
            raise ValueError("%s is not a Mcu enum" % (mcu_type))
        if mcu_type == McuType.ProMicro:
            self.record_part(_Part.ProMicro)
            part = skidl.Part('keycad',
                              'ProMicro',
                              skidl.NETLIST,
                              footprint='keycad:ArduinoProMicro')
            part.ref = self.assign_ref(_RefType.IC)
            part.value = 'Pro Micro'
            return part

        if mcu_type == McuType.BluePill:
            self.record_part(_Part.BluePill)
            part = skidl.Part('keycad',
                              'BluePill_STM32F103C',
                              skidl.NETLIST,
                              footprint='keycad:BluePill_STM32F103C')
            part.ref = self.assign_ref(_RefType.IC)
            part.value = 'Blue Pill'
            return part
        raise ValueError("MCU type %s not implemented" % mcu_type)

    def get_keyswitch(self, value, is_mx, is_hotswap):
        if is_mx:
            switch_type = "MX"
        else:
            switch_type = "PG1350"
        if is_hotswap:
            socket_type = "Kailh_socket"
        else:
            socket_type = "SW"
        footprint = "keycad:%s_%s" % (socket_type, switch_type)

        if is_mx:
            self.record_part(_Part.MxSw)
            if is_hotswap:
                self.record_part(_Part.MxKailh)
        else:
            self.record_part(_Part.Pg1350Sw)
            if is_hotswap:
                self.record_part(_Part.Pg1350Kailh)

        part = skidl.Part('keycad',
                          'KEYSW',
                          skidl.NETLIST,
                          footprint=footprint)
        part.ref = self.assign_ref(_RefType.Keyswitch)
        part.value = value
        return part

    def get_per_key_rgb_led(self):
        self.record_part(_Part.Sk6812MiniE)
        part = skidl.Part('keycad',
                          'SK6812MINI-E',
                          skidl.NETLIST,
                          footprint='keycad:SK6812-MINI-E-BOTTOM')
        part.ref = self.assign_ref(_RefType.LED)
        part.value = "SK6812MINI-E"
        return part

    def get_capacitor(self, value):
        part = skidl.Part('keycad',
                          'C',
                          skidl.NETLIST,
                          footprint='keycad:C_0805_2012Metric')
        if value == "0.1uF":
            self.record_part(_Part.C0UF1)
            part.value = value
        else:
            raise ValueError("Unknown capacitor value")
        part.ref = self.assign_ref(_RefType.Capacitor)
        return part

    def get_diode(self):
        self.record_part(_Part.D1N4148)
        part = skidl.Part('keycad',
                          'D',
                          skidl.NETLIST,
                          footprint='keycad:D_0805')
        part.ref = self.assign_ref(_RefType.Diode)
        part.value = "1N4148"
        return part

    def get_resistor(self, value):
        part = skidl.Part('keycad',
                          'R',
                          skidl.NETLIST,
                          footprint='keycad:R_0805_2012Metric')
        if value == "5K1":
            self.record_part(_Part.R5K1)
            part.value = value
        else:
            raise ValueError("Unknown resistor value")
        part.ref = self.assign_ref(_RefType.Resistor)
        return part

    def get_reset_switch(self):
        self.record_part(_Part.SWSKQG)
        part = skidl.Part('keycad',
                          'SW_Push',
                          skidl.NETLIST,
                          footprint='keycad:SW_SPST_SKQG_WithoutStem')
        part.ref = self.assign_ref(_RefType.Switch)
        part.value = 'SKQGAKE010'
        return part

    def get_usb_c_connector(self):
        self.record_part(_Part.USB_HRO_C31M14)
        part = skidl.Part(
            'keycad',
            'USB_C_Receptacle_USB2.0',
            skidl.NETLIST,
            footprint='keycad:USB_C_Receptacle_HRO_TYPE-C-31-M-14')
        part.ref = self.assign_ref(_RefType.Connector)
        part.value = 'TYPE-C-31-M-14'
        return part
