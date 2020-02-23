import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Parser:
    def __init__(self):
        self.reset()

    def reset(self):
        self.__key_count = 0
        self.__row_index = 0
        self.__col_index = 0

    @property
    def key_count(self):
        return self.__key_count

    def _process_row_metadata(self, metadata):
        pass

    def _process_key_metadata(self, metadata):
        if 'w' in metadata:
            pass
            #self.__pcb.set_logical_key_width(float(metadata['w']))

    def _process_key(self, key):
        logger.info("processing key '%s'" % (key))
        self.__key_count += 1

    def _process_row(self, row):
        self.__col_index = 0
        for key in row:
            if isinstance(key, dict):
                self._process_key_metadata(key)
            else:
                self._process_key(key)
                self.__col_index += 1
                #self.__pcb.advance_cursor()

    def handle_dict(self, kle_dict):
        for row in kle_dict:
            if isinstance(row, dict):
                self._process_row_metadata(row)
            else:
                self._process_row(row)
                self.__row_index += 1
                #self.__pcb.cursor_carriage_return()

    def load(self, filename):
        self.reset()
        with open(filename, "r") as f:
            self.handle_dict(json.loads(f.read()))
