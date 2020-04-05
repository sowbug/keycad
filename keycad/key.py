class Key:
    def __init__(self, x, y, text='none', width=1, height=1, is_homing=False):
        self.__labels = text.split("\n")
        self.__x = x
        self.__y = y
        self.__width = width
        self.__height = height
        self.__is_homing = is_homing

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
