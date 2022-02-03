#!/usr/local/bin/python3.10

import re

####################################################################################################

# Tokenizer: takes texts and turns it into "words" (tokens)

from dataclasses import dataclass

@dataclass(init=True, eq=True, repr=True)
class Pos:
    idx: int = -1
    col: int = -1
    ln: int = -1

@dataclass(init=True, repr=True, eq=True)
class Token:
    name: str = ''
    value: str = ''
    pos_begin: Pos = Pos()
    pos_end: Pos = Pos()
    def __repr__(self):
        begin = self.pos_begin.ln, self.pos_begin.col
        end = self.pos_end.ln, self.pos_end.col
        return f'Token({self.name}, {repr(self.value)}, {(begin)}-{end})'
    __str__ = __repr__

data_types = ['int', 'float', 'string', 'boolean', 'array', 'null']

language_words = ['const', 'int', 'float', 'string', 'array', 'null', 'true', 'false', 'boolean',
                  'is', 'IS', 'not', 'and', 'or',
                  'break', 'continue', 'if', 'do', 'then', 'while', 'foreach', 'match', 'case', 'end',
                  'function', 'return', 'returns']

punctuation = [';', ':', ',', '[', ']', '{', '}', '(', ')', ':=', '=', '=>', '+', '-', '*', '**', '/', '//', '%', '~', '&', '|', '>>', '<<',
               '<', '<=', '>', '>=', '==', '!=' , '+=', '++']

punctuation_dict = \
{ 
   ';'  : 'SEMICOLON',
   ':'  : 'COLON',
   ','  : 'COMMA',
   '['  : 'LEFT_SQUARE_BRACKET',
   ']'  : 'RIGHT_SQUARE_BRACKET',
   '{'  : 'LEFT_CURLY_BRACE',
   '}'  : 'RIGHT_CURLY_BRACE',
   '('  : 'LEFT_PARENTHESES',
   ')'  : 'RIGHT_PARENTHESES',
   ':=' : 'COLON_EQUAL',
   '='  : 'EQUAL',
   '=>' : 'RETURN_ARROW',
   '+'  : 'PLUS',
   '-'  : 'MINUS',
   '*'  : 'STAR',
   '**' : 'DOUBLE_STAR',
   '/'  : 'SLASH',
   '//' : 'DOUBLE_SLASH',
   '%'  : 'PERCENT',
   '~'  : 'TILDE',
   '&'  : 'AND',
   '|'  : 'PIPE',
   '>>' : 'RIGHT_SHIFT',
   '<<' : 'LEFT_SHIFT',
   '<'  : 'LESS',
   '<=' : 'LESS_EQUAL',
   '>'  : 'GREATER',
   '>=' : 'GREATER_EQUAL',
   '==' : 'EQUAL_EQUAL',
   '!=' : 'NOT_EQUAL',
   '+=' : 'PLUS_EQUAL',
   '++' : 'PLUS_PLUS',
}

followers = {
    '=', '>', '<', '+', '*'
}

int_pattern = re.compile(r'[+-]{0,1}\d+([eE][+-]{0,1}\d+){0,1}')
float_pattern = re.compile(r'[+-]{0,1}\d+[.]\d*([eE][+-]{0,1}\d+){0,1}|[+-]{0,1}\d*[.]\d+([eE][+-]{0,1}\d+){0,1}')
number_pattern = re.compile(float_pattern.pattern + '|' + int_pattern.pattern)
string_pattern = re.compile(r'f{0,1}".*?(?<!\\)"')

class Tokenizer:
    def __init__(self, text: str):
        self.text: str = text
        self.current_char: str = ''
        self.idx, self.ln, self.col = -1, -1, -1
        if len(text) != 0:
            self.idx, self.ln, self.col = 0, 0, 0
            self.current_char = self.text[0]
        self.tokens_list: list[Token] = []

    def pos(self):
        return Pos(self.idx, self.col, self.ln)

    def next_token(self) -> Token | None:
        token = None
        if self.current_char != '': # it is not EOF
            if self.current_char == '\n':
                # NEWLINE
                token = Token(name='NEWLINE', value='\n', pos_begin=self.pos())
                token.pos_end = Pos(self.idx+1, self.col+1, self.ln)
                self.idx += 1
                if self.idx < len(self.text):
                    self.current_char = self.text[self.idx]
                    self.col = 0
                    self.ln += 1
                else:
                    self.current_char= ''

            elif self.current_char == '#':
                # COMMENT
                next_new_line = self.text.find('\n', self.idx) # NEWLINE is the only thing that stops a comment
                token = Token(name='COMMENT')
                token.pos_begin = self.pos()
                if next_new_line != -1:
                    # this comment is not in last line
                    token.value = self.text[self.idx:next_new_line]
                    self.idx = next_new_line
                    self.current_char = '\n'
                else:
                    # this comment is in last line
                    token.value = self.text[self.idx:]
                    self.idx = len(self.text)
                    self.current_char = ''
                self.col += len(token.value)
                token.pos_end = Pos(token.pos_begin.idx+len(token.value), token.pos_begin.col+len(token.value), self.ln)

            elif string := string_pattern.match(string=self.text, pos=self.idx):
                match_value = string.group()
                token = Token(name='f-string' if match_value[0] == 'f' else 'string', value=match_value)
                begin = self.pos()
                token.pos_begin = begin
                self.idx = string.end()
                self.col += len(token.value)
                if self.idx < len(self.text):
                    self.current_char = self.text[self.idx]
                else:
                    self.current_char = ''
                token.pos_end = Pos(begin.idx+len(token.value), begin.col+len(token.value), begin.ln)

            elif re.match(pattern=r'[_a-zA-Z]', string=self.current_char):
                # an identifier or a keyword, search for nearest delimiter, (any non-identifier character)
                next_delimiter = re.compile(r'[^_0-9a-zA-Z]').search(string=self.text, pos=self.idx)
                begin = self.pos()
                token = Token(pos_begin=begin)
                if next_delimiter is not None:
                    # we have not reached End Of File
                    token.value = self.text[self.idx: next_delimiter.start()]
                    self.idx = next_delimiter.start()
                    self.current_char = self.text[self.idx]
                else:
                    # we reached End Of File
                    token.value = self.text[self.idx:]
                    self.idx = len(self.text)
                    self.current_char = ''
                self.col += len(token.value)
                token.pos_end = Pos(begin.idx+len(token.value), begin.idx+len(token.value), self.ln)
                if token.value in language_words:
                    token.name = 'KEYWORD'
                else:
                    if self.tokens_list[-1].name:
                        pass
                    token.name = 'NAME'

            elif self.current_char in punctuation:
                begin = self.pos()
                token = Token(pos_begin=begin)
                if self.idx + 1 < len(self.text) and self.text[self.idx + 1] in followers:
                    # Things like :=, ==, !=, <=, <<
                    token.value = self.text[self.idx:self.idx+2]
                else:
                    # Things like +, -, /, *, any thing single character
                    token.value = self.text[self.idx:self.idx+1]
                
                self.idx += len(token.value)
                self.col += len(token.value)
                
                if self.idx < len(self.text):
                    # Not Just Yet
                    self.current_char = self.text[self.idx]
                else:
                    # End Of File
                    self.current_char = ''
                token.name = punctuation_dict[token.value]
                token.pos_end = Pos(begin.idx+len(token.value), begin.col+len(token.value), self.ln)

            elif re.match(pattern=r'[.0-9]', string=self.current_char):
                # A NUMBER
                number_match = number_pattern.search(string=self.text, pos=self.idx)
                begin =   self.pos()
                token =   Token(name='NUMBER', value=number_match.group(), pos_begin=begin)
                end   =   Pos(token.pos_begin.idx + len(token.value), token.pos_begin.col + len(token.value), self.ln)
                token.pos_end = end
                self.idx = number_match.end()
                self.col += len(token.value)
                if self.idx < len(self.text):
                    self.current_char = self.text[self.idx]
                else:
                    self.current_char = ''
            else:
                # This is for characters like spaces, like in 1 + 2
                # spaces around + are redundant and dont affect sematics
                if self.idx + 1 < len(self.text):
                    self.idx += 1
                    self.current_char = self.text[self.idx]
                else:
                    # End Of File
                    self.current_char = ''
                    self.idx = len(self.text)
                self.col += 1
        self.tokens_list.append(token)
        return token

    def __iter__(self):
        while True:
            t = self.next_token()
            if t is not None:
                yield t
            if self.current_char == '':
                break
####################################################################################################

# run
from sys import argv
if len(argv) == 3 and argv[1].lower() == '-f':
    with open(argv[2], 'r') as source_file:
        source = str(source_file.read())
        for t in Tokenizer(source):
            print(t)
else:
    source = argv[1]
    for t in Tokenizer(source):
        print(t)
