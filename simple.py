
#####################################################################################################
# TOKENS
COMMENT_TOKEN = 'COMMENT'

class Token:
    def __init__(self, name, value):
        self.name, self.value = name, value

    def __repr__(self):
        return f'Token({self.name}, {self.value})'

#####################################################################################################

class Parser:
    def __init__(self, text: str):
        self.text: str = self.text
        self.current_char: str = ''
        # self.current_char is None when EOF
        self.index, self.column, self.line = -1, -1, -1

    def advance(self):
        if self.index+1 < len(self.text):
            # we can advance if still have more text to parse
            self.index += 1
            self.current_char = self.text[self.index]
            if self.current_char == '\n':
                # we reached line end
                self.column = 0
                self.line += 1
        return self
    
    def next_token(self):
        while self.current_char != None:
            pass

#####################################################################################################

from sys import argv
with open(argv[0], 'r') as source:
    parser = Parser(str(source.read()))
