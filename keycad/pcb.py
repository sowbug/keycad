import json

KC_TO_MM = 1000000

class Pcb:
    def __init__(self, mx_key_width):
        self.__mx_key_width = mx_key_width
        self.__logical_key_width = 1
        self.__key_cursor_x = 0
        self.__key_cursor_y = 0
        self.reset_key_attributes()

        self.__kinjector_json = {}

    def read_positions(self, filename):
        with open(filename, "r") as f:
            self.__kinjector_json = json.loads(f.read())

    def set_logical_key_width(self, width):
        self.__logical_key_width = width

    def reset_key_attributes(self):
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
        self.reset_key_attributes()

    def cursor_carriage_return(self):
        self.__key_cursor_x = 0
        self.__key_cursor_y += self.__mx_key_width

    def place_component(self, part, x, y, angle, side):
        self.__kinjector_json[part.ref] = {
            'position': {
                'x': x,
                'y': y,
                'angle': angle,
                'side': side
            }
        }

    def mark_component_position(self, part, x_offset, y_offset, angle, side):
        x, y = self.get_part_position()
        x = (x + x_offset) * KC_TO_MM
        y = (y + y_offset) * KC_TO_MM
        (x, y, angle,
         side) = self.maybe_override_position(part, x, y, angle, side)
        self.place_component(part, x, y, angle, side)

    def place_component_on_keyboard_grid(self, part, x, y, angle, side):
        x = (x * self.__mx_key_width) * KC_TO_MM
        y = (y * self.__mx_key_width) * KC_TO_MM
        self.place_component(part, x, y, angle, side)

    def mark_switch_position(self, part):
        self.mark_component_position(part, 0, 0, 180, 'top')

    def mark_diode_position(self, part):
        x_offset, y_offset = (5, -self.__mx_key_width / 5)
        self.mark_component_position(part, x_offset, y_offset, 90, 'bottom')

    def mark_led_position(self, part):
        x_offset, y_offset = (0, -self.__mx_key_width / 4)
        self.mark_component_position(part, x_offset, y_offset, 0, 'bottom')

    def mark_pro_micro_position(self, part):
        x, y = 30, -50
        self.mark_component_position(part, x, y, 0, 'top')

    def mark_reset_switch_position(self, part):
        x, y = 50, -50
        self.mark_component_position(part, x, y, 0, 'bottom')

    def get_kinjector_dict(self):
        return self.__kinjector_json

    def place_pro_micro(self, pro_micro):
        self.mark_pro_micro_position(pro_micro)

    def place_reset_switch(self, reset):
        self.mark_reset_switch_position(reset)
