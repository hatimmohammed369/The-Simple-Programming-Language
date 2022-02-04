#!/usr/local/bin/python3.10

import re
from typing import Any
from snoop import snoop

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
    value: Any = object()
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
indent_pattern = re.compile(r'[ ]{4}|[\t]') # 4 consecutive spaces or a single tab

class Tokenizer:
    def __init__(self, text: str):
        self.text: str = text
        self.current_char: str = ''
        self.idx, self.ln, self.col = 0, 0, 0
        if len(text) != 0:
            self.current_char = self.text[0]
        self.tokens_list: list[Token] = []
        self.identifiers_table: dict[str, list[Token]] = {}
        self.indentation: str = ''
        self.indent_level = 0 # how many indents in currently
        self.dents_list: list[Token] = [] # stores indents and dedents

    def __len__(self):
        return len(self.tokens_list)

    def __getitem__(self, key) -> Token:
        return self.tokens_list[key]

    def pos(self):
        return Pos(self.idx, self.col, self.ln)

    def current_line(self) -> str:
        previous_line_break = self.text.rfind('\n', 0, self.idx)
        if previous_line_break == -1:
            # it's first line
            previous_line_break = 0
        
        next_line_break = self.text.find('\n', self.idx)
        if next_line_break == -1:
            # it's last line
            next_line_break = len(self.text)
        return self.text[previous_line_break + 1 : next_line_break]

    def next_token(self) -> tuple[Token | None, str | None]:
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
                    self.current_char = '\n'
                else:
                    # this comment is in last line
                    token.value = self.text[self.idx:]
                    self.current_char = ''
                self.idx += len(token.value)
                self.col += len(token.value)
                token.pos_end = Pos(token.pos_begin.idx+len(token.value), token.pos_begin.col+len(token.value), self.ln)

            elif string := string_pattern.match(string=self.text, pos=self.idx):
                # STRING
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
                # IDENTIFIER
                # an identifier or a keyword, search for nearest delimiter, (any non-identifier character)
                next_delimiter = re.compile(r'[^_0-9a-zA-Z]').search(string=self.text, pos=self.idx)
                current_identifier = ''
                if next_delimiter is not None:
                    # we have not reached End Of File
                    current_identifier = self.text[self.idx: next_delimiter.start()]
                else:
                    # we reached End Of File
                    current_identifier = self.text[self.idx:]
                
                begin = self.pos()
                token = Token(pos_begin=begin)
                token.value = current_identifier
                self.idx += len(token.value)
                self.col += len(token.value)
                token.pos_end = Pos(begin.idx+len(token.value), begin.idx+len(token.value), self.ln)
                
                if self.idx < len(self.text):
                    self.current_char = self.text[self.idx]
                else:
                    # End Of File
                    self.current_char = ''
                
                if token.value in language_words:
                    token.name = 'KEYWORD'
                else:
                    if current_identifier in self.identifiers_table:
                        # we met this identifier before
                        token.name = self.identifiers_table[token.value][-1].name
                        self.identifiers_table[token.value].append(token)
                    else:
                        # A new identifier
                        self.identifiers_table[token.value] = [token]
                        if len(self) >= 2 and self.tokens_list[-1].value in data_types and self.tokens_list[-2].value == 'const':
                            # things like: const boolean p := true;
                            token.name = 'CONST_NAME'
                        else:
                            token.name = 'NAME'

            elif self.current_char in punctuation:
                # SOMETHING LIKE *, +, {, %, ;, .....
                begin = self.pos()
                token = Token(pos_begin=begin)
                if self.idx + 1 < len(self.text) and self.text[self.idx + 1] in followers:
                    # Things like :=, ==, !=, <=, <<
                    token.value = self.text[self.idx:self.idx+2]
                else:
                    # Things like +, -, /, *, any thing single character
                    token.value = self.text[self.idx:self.idx+1]
                    if self[-1].name == 'CONST_NAME' and token.value == '=':
                        # Constant re-assignment, illegal
                        error = '\nConstant re-assignment error:\n' + self.current_line() + '\n' + (' ' * self.col)
                        error += '^\n' + (' ' * self.col) + f'Constant ({self[-1].value}) re-assignment\n'
                        return None, error
                
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
        if token is not None:
            # we have a valid token
            self.tokens_list.append(token)
        return token, None

    def __iter__(self):
        while True:
            token, error = None, None
            if self.col == 0:
                # Check for indentation
                next_line_break = self.text.find('\n', self.idx)
                if self.text.find('\n', self.idx) == self.idx or re.compile(r'\s+').match(string=self.text[self.idx:next_line_break]):
                    # this line is empty or it is just whitespaces
                    self.idx = next_line_break
                    self.col += 1
                    self.current_char = '\n'
                    continue
                else:
                    # this line contains some non-whitespaces
                    current_line = self.current_line()
                    first_non_white_space = re.compile(r'[^\s]').search(string=current_line).start()
                    captured_indent = self.text[self.idx:first_non_white_space]
                    error = None
                    if ' ' in captured_indent and '\t' in captured_indent:
                        # Syntax Error: Mixing spaces and tabs in indentation
                        error  = f'Line {self.ln + 1}:\n'
                        error += ' ' + current_line + '\n'
                        error += '^' * len(captured_indent)
                    if self.ln == 0 and len(captured_indent) != 0:
                        # if it is first line, this is Syntax Error
                        error  = 'Line 1:\n'
                        error += ' ' + current_line + '\n'
                        error += '^' * len(captured_indent)
                    if error is not None:
                        # this is not first line
                        level = len(captured_indent) // 4
                        begin = self.pos()
                        token = Token(value=captured_indent, pos_begin=begin)
                        token.pos_end = Pos(begin.idx+len(captured_indent), begin.col+len(captured_indent), self.ln)
                        if level < self.indent_level:
                            # DEDENT
                            self.indent_level -= 1
                            token.name = 'DEDENT'
                        elif self.indent_level < level:
                            # INDENT
                            self.indent_level += 1
                            token.name = 'INDENT'
                        self.idx += len(token.value)
                        self.col += len(token.value)
                        if self.idx < len(self.text):
                            self.current_char = self.text[self.idx]
                        else:
                            self.current_char = ''
            else:
                token, error = self.next_token()
            #
            #
            if error is not None:
                print(error)
                exit(0)
            if token is not None:
                yield token
            if self.current_char == '':
                # DONE!
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
    source = """write(0)
function f() returns int => {
    write("empty fucntion");
}"""
    for t in Tokenizer(source):
        print(t)
