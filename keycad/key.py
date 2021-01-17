# https://docs.qmk.fm/#/keycodes
SYMBOL_TO_ALNUM = {
    "!": 'EXCL',
    "": 'SPC',
    "#": 'HASH',
    "$": 'DLR',
    "%": 'PCT',
    "&": 'AMP',
    "'": 'QUOT',
    "(": 'LPRN',
    ")": 'RPRN',
    "*": 'AST',
    ",": "COMM",
    "-": 'MINS',
    ".": "DOT",
    "/": "SLSH",
    ";": "SCLN",
    "=": 'EQL',
    "@": 'AT',
    "Alt": "LALT",
    "Backspace": "BSPC",
    "Caps Lock": 'CAPS',
    "Command": "LGUI",
    "Control": "LCTRL",
    "Ctrl": "LCTRL",
    "Enter": "ENT",
    "Esc": "ESC",
    "Left Alt": "LALT",
    "Left Ctrl": "LCTRL",
    "Left Shift": "LSFT",
    "Left Win": "LGUI",
    "OS": "LGUI",
    "Right Alt": "RALT",
    "Right Ctrl": "RCTRL",
    "Right Shift": "RSFT",
    "Right Win": "RGUI",
    "Win": "LGUI",
    "[": "LBRC",
    "\\": "BSLS",
    "]": "RBRC",
    "^": 'CRT',
    "`": 'GRV',
    "|": 'BAR',
    "←": 'LEFT',
    "↑": 'UP',
    "→": 'RGHT',
    "↓": 'DOWN',
    "⌘": "LGUI",
    "PrtSc": 'PSCREEN',
    "Scroll Lock": 'SCROLL',
    "Pause": 'BREAK',
}


class Key:
    def __init__(self, x, y, text='none', width=1, height=1, is_homing=False):
        self.__labels = text.split("\n")
        self.__x = x
        self.__y = y
        self.__width = width
        self.__height = height
        self.__is_homing = is_homing
        self.__matrix_row = -1
        self.__matrix_col = -1
        self.__led_x = -1
        self.__led_y = -1
        self.__led_identifier = -1

    @property
    def labels(self):
        return self.__labels

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    @property
    def led_x(self):
        return self.__led_x

    @property
    def led_y(self):
        return self.__led_y

    @led_x.setter
    def led_x(self, x):
        self.__led_x = int(x)

    @led_y.setter
    def led_y(self, y):
        self.__led_y = int(y)

    @property
    def led_identifier(self):
        return self.__led_identifier

    @led_identifier.setter
    def led_identifier(self, id):
        self.__led_identifier = id

    @property
    def width(self):
        return self.__width

    @property
    def height(self):
        return self.__height

    @property
    def is_homing(self):
        return self.__is_homing

    def __str__(self):
        return "%s [%.2f %.2f]" % (self.__labels[0], self.x, self.y)

    @property
    def position(self):
        return ((self.x + (self.width - 1) / 2,
                 self.y + (self.height - 1) / 2))

    @property
    def matrix_row(self):
        return self.__matrix_row

    @property
    def matrix_col(self):
        return self.__matrix_col

    @property
    def rowcol_label(self):
        return "R%dC%d" % (self.matrix_row, self.matrix_col)

    def get_rowcol_label_dict(self, width_mm, height_mm):
        x, y = self.position
        x += 0.1
        y += 0.3
        return {
            "text": self.rowcol_label,
            "x_mm": x * width_mm,
            "y_mm": y * height_mm
        }

    @property
    def matrix_identifier(self):
        return "%s%d" % (chr(ord('A') + self.matrix_row), self.matrix_col)

    @matrix_row.setter
    def matrix_row(self, row):
        self.__matrix_row = row

    @matrix_col.setter
    def matrix_col(self, col):
        self.__matrix_col = col

    @property
    def qmk_keycode(self):
        label = self.printable_label.upper()
        return "KC_%s" % (label)

    @property
    def printable_label(self):
        if len(self.__labels) > 1:
            label = self.__labels[1]
        else:
            label = self.__labels[0]
        if label in SYMBOL_TO_ALNUM:
            return SYMBOL_TO_ALNUM[label]
        return label
