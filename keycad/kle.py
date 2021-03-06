'''
kle knows about keyboard-layout-editor.com JSON files.
'''

import json
import logging

from keycad import key

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Parser:
    def __init__(self):
        self.reset()

    def reset(self):
        self.__keys = []
        self.__cursor_x = 0
        self.__cursor_y = 0
        self._board_left = 99999
        self._board_top = 99999
        self._board_right = 0
        self._board_bottom = 0
        self._max_col_count = 0
        self._col_count = 0
        self._row_count = 0
        self.reset_row_parameters()
        self.reset_key_parameters()

    def reset_row_parameters(self):
        self.__current_row_height = 1

    def reset_key_parameters(self):
        self.__current_key_width = 1
        self.__current_key_height = 1
        self.__current_key_x_padding = 0
        self.__current_key_y_padding = 0
        self.__current_key_is_homing = False

    @property
    def key_count(self):
        return len(self.keys)

    @property
    def row_count(self):
        return self._row_count

    @property
    def max_col_count(self):
        return self._max_col_count

    @property
    def keys(self):
        return self.__keys

    @property
    def board_left(self):
        return self._board_left

    @property
    def board_top(self):
        return self._board_top

    @property
    def board_right(self):
        return self._board_right

    @property
    def board_bottom(self):
        return self._board_bottom

    def _process_row_metadata(self, metadata):
        pass

    def _process_key_metadata(self, metadata):
        if 'h' in metadata:
            self.__current_key_height = float(metadata['h'])
        if 'w' in metadata:
            self.__current_key_width = float(metadata['w'])
        if 'x' in metadata:
            self.__current_key_x_padding = float(metadata['x'])
        if 'y' in metadata:
            self.__current_key_y_padding = float(metadata['y'])
        if 'n' in metadata:
            self.__current_key_is_homing = True

    def _process_key(self, k):
        logger.info("processing key '%s'" % (k))
        new_key = key.Key(self.__cursor_x + self.__current_key_x_padding,
                          self.__cursor_y,
                          text=k,
                          width=self.__current_key_width,
                          height=self.__current_key_height,
                          is_homing=self.__current_key_is_homing)
        self.__keys.append(new_key)
        if new_key.x < self._board_left:
            self._board_left = new_key.x
        if new_key.y < self._board_top:
            self._board_top = new_key.y
        if new_key.x + self.__current_key_width > self._board_right:
            self._board_right = new_key.x + self.__current_key_width
        if new_key.y + self.__current_key_height > self._board_bottom:
            self._board_bottom = new_key.y + self.__current_key_height

    def _process_row(self, row):
        self.reset_row_parameters()
        self.__cursor_x = 0
        self._row_count += 1
        self._col_count = 0
        first_key_in_row = True
        for key in row:
            if isinstance(key, dict):
                self._process_key_metadata(key)
            else:
                if first_key_in_row:
                    first_key_in_row = False
                    self.__cursor_y += self.__current_key_y_padding
                self._process_key(key)
                self.__cursor_x += (self.__current_key_width +
                                    self.__current_key_x_padding)
                self._col_count += 1
                if self._col_count > self._max_col_count:
                    self._max_col_count = self._col_count
                self.reset_key_parameters()

    def handle_dict(self, kle_dict):
        for row in kle_dict:
            if isinstance(row, dict):
                self._process_row_metadata(row)
            else:
                self._process_row(row)
                self.__cursor_x = 0
                self.__cursor_y += self.__current_row_height

    def load(self, filename):
        self.reset()
        with open(filename, "r") as f:
            self.handle_dict(json.loads(f.read()))
