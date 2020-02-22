import json

class Parser:
    def __init__(self):
        self.__row_index = 0
        self.__col_index = 0

    def process_row_metadata(self, metadata):
        pass

    def process_key_metadata(self, metadata):
        if 'w' in metadata:
            pass
            #self.__pcb.set_logical_key_width(float(metadata['w']))

    def process_key(self, key):
        pass

    def process_row(self, row):
        self.__col_index = 0
        for key in row:
            if isinstance(key, dict):
                self.process_key_metadata(key)
            else:
                self.process_key(key)
                self.__col_index += 1
                #self.__pcb.advance_cursor()

    def handle_json(self, json):
        for row in json:
            if isinstance(row, dict):
                self.process_row_metadata(row)
            else:
                self.process_row(row)
                self.__row_index += 1
                #self.__pcb.cursor_carriage_return()

    def load(self, filename):
        with open(filename, "r") as f:
            self.handle_json(json.loads(f.read()))
