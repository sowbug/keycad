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

    @property
    def key_count(self):
        return len(self.keys)

    @property
    def keys(self):
        return self.__keys

    def _process_row_metadata(self, metadata):
        pass

    def _process_key_metadata(self, metadata):
        if 'w' in metadata:
            self.__current_key_width = float(metadata['w'])

    def _process_key(self, k):
        logger.info("processing key '%s'" % (k))
        new_key = key.Key(self.__cursor_x,
                          self.__cursor_y,
                          text=k,
                          width=self.__current_key_width,
                          height=self.__current_key_height)
        self.__keys.append(new_key)

    def _process_row(self, row):
        self.reset_row_parameters()
        self.__cursor_x = 0
        for key in row:
            if isinstance(key, dict):
                self._process_key_metadata(key)
            else:
                self._process_key(key)
                self.__cursor_x += self.__current_key_width
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
