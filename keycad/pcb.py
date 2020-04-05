import json

KC_TO_MM = 1000000


class Pcb:
    def __init__(self, mx_key_width, mx_key_height):
        self.__mx_key_width = mx_key_width
        self.__mx_key_height = mx_key_height
        self.__logical_key_width = 1
        self.__key_cursor_x = 0
        self.__key_cursor_y = 0
        self._reset_key_attributes()

        self.__kinjector_json = {}

    @property
    def kinjector_dict(self):
        return self.__kinjector_json

    def read_positions(self, filename):
        with open(filename, "r") as f:
            self.__kinjector_json = json.loads(f.read())

    def _reset_key_attributes(self):
        self.__logical_key_width = 1

    def get_part_position(self):
        x = int((self.__key_cursor_x +
                 ((self.__logical_key_width - 1) * self.__mx_key_width / 2)))
        y = int(self.__key_cursor_y)
        return (x, y)

    def maybe_override_position(self, part, x, y, angle, side):
        m = self.__kinjector_json['board']['modules']
        if part.ref in m and 'position' in m[part.ref]:
            m = m[part.ref]['position']
            k = 'angle'
            if k in m:
                angle = m[k]
            k = 'side'
            if k in m:
                side = m[k]
            k = 'x'
            if k in m:
                x = m[k]
            k = 'y'
            if k in m:
                y = m[k]
        return (x, y, angle, side)

    def advance_cursor(self, end_of_row=False):
        self.__key_cursor_x += self.__mx_key_width * self.__logical_key_width
        self._reset_key_attributes()

    def cursor_carriage_return(self):
        self.__key_cursor_x = 0
        self.__key_cursor_y += self.__mx_key_height

    def _inject_component(self, part, x, y, angle, side):
        self.__kinjector_json[part.ref] = {
            'position': {
                'x': x,
                'y': y,
                'angle': angle,
                'side': side
            }
        }

    def convert_keyboard_grid_to_kicad_units(self, x, y, x_offset, y_offset):
        return ((x * self.__mx_key_width + x_offset) * KC_TO_MM,
                (y * self.__mx_key_width + y_offset) * KC_TO_MM)

    def place_component_on_keyboard_grid(self,
                                         part,
                                         x,
                                         y,
                                         angle,
                                         side,
                                         x_offset=0,
                                         y_offset=0):
        (x, y) = self.convert_keyboard_grid_to_kicad_units(
            x, y, x_offset, y_offset)
        (x, y, angle,
         side) = self.maybe_override_position(part, x, y, angle, side)
        self._inject_component(part, x, y, angle, side)

    def place_keyswitch_on_keyboard_grid(self, part, key):
        (x, y) = key.position
        x_offset, y_offset = (0, 0)
        self.place_component_on_keyboard_grid(part,
                                              x,
                                              y,
                                              0,
                                              'top',
                                              x_offset=x_offset,
                                              y_offset=y_offset)

    def place_led_on_keyboard_grid(self, part, key):
        (x, y) = key.position

        # The number 3.772277228 is backed out from a spec placing an
        # MX Cherry SMD LED 5.05mm above the switch center. I'm not aware
        # of an equivalent spec for Kailh Choc switches. In that case
        # we'll scale it linearly with the switch height. 
        x_offset, y_offset = (0, -self.__mx_key_height / 3.772277228)
        self.place_component_on_keyboard_grid(part,
                                              x,
                                              y,
                                              0,
                                              'bottom',
                                              x_offset=x_offset,
                                              y_offset=y_offset)

    def place_diode_on_keyboard_grid(self, part, key):
        (x, y) = key.position
        x_offset, y_offset = (-5, -self.__mx_key_width / 5)
        self.place_component_on_keyboard_grid(part,
                                              x,
                                              y,
                                              90,
                                              'bottom',
                                              x_offset=x_offset,
                                              y_offset=y_offset)

    def place_pro_micro_on_keyboard_grid(self, part):
        self.place_component_on_keyboard_grid(part, 10, 3, 0, 'top')

    def place_blue_pill_on_keyboard_grid(self, part):
        self.place_component_on_keyboard_grid(part, 10, 3, 0, 'top')

    def place_reset_switch_on_keyboard_grid(self, part):
        self.place_component_on_keyboard_grid(part, 10, 4, 180, 'bottom')

    def place_usb_c_connector_on_keyboard_grid(self, part):
        self.place_component_on_keyboard_grid(part, 10, 0, 180, 'bottom')

    def write_kinjector_file(self, filename):
        with open(filename, "w") as f:
            f.write(
                json.dumps({'board': {
                    'modules': self.__kinjector_json
                }},
                           sort_keys=True,
                           indent=4))
