# KiCad explodes with raw quote
# freerouting.jar explodes with raw backtick
SYMBOL_TO_ALNUM = {
    "'": 'QUOT',
    "`": 'GRV',
    "↑": 'UP',
    "↓": 'DOWN',
    "←": 'LEFT',
    "→": 'RGHT',
    "": 'SPC',
    "|": 'BAR',
    "!": 'EXCL',
    "@": 'AT',
    "#": 'HASH',
    "$": 'DLR',
    "%": 'PCT',
    "^": 'CRT',
    "&": 'AMP',
    "*": 'AST',
    "(": 'LPRN',
    ")": 'RPRN',
    "-": 'MINS',
    "=": 'EQL',
    "Caps Lock": 'CAPS',
    "Shift": 'SHFT',
    "Backspace": "BSPC",
    "Enter": "ENT",
    "[": "LBRC",
    "]": "RBRC",
    "Esc": "ESC",
    "\\": "BSLS",
    ";": "SCLN",
    ",": "COMM",
    ".": "DOT",
    "/": "SLSH",
    "CTRL": "LCTRL",
    "WIN": "LGUI"
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
