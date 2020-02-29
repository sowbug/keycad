class Key:
    def __init__(self, x, y, text='none', width=1, height=1):
        self.__labels = text.split("\n")
        self.__x = x
        self.__y = y
        self.__width = width
        self.__height = height

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