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
    def keys(self):
        return self.__keys

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
                          self.__cursor_y + self.__current_key_y_padding,
                          text=k,
                          width=self.__current_key_width,
                          height=self.__current_key_height,
                          is_homing=self.__current_key_is_homing)
        self.__keys.append(new_key)

    def _process_row(self, row):
        self.reset_row_parameters()
        self.__cursor_x = 0
        for key in row:
            if isinstance(key, dict):
                self._process_key_metadata(key)
            else:
                self._process_key(key)
                self.__cursor_x += (self.__current_key_width +
                                    self.__current_key_x_padding)
                self.reset_key_parameters()

    def handle_dict(self, kle_dict):
        for row in kle_dict:
            if isinstance(row, dict):
                self._process_row_metadata(row)
            else:
                self._process_row(row)
                self.__cursor_x = 0
                # TODO(miket): I'm not sure about the y padding.
                # That seems more like an attribute of the whole row
                self.__cursor_y += (self.__current_row_height +
                                    self.__current_key_y_padding)

    def load(self, filename):
        self.reset()
        with open(filename, "r") as f:
            self.handle_dict(json.loads(f.read()))
