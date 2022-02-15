#!/usr/local/bin/python3.10

import re
from typing import Any

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

data_types = ('int', 'float', 'string', 'boolean', 'array', 'null')

language_words = ('const', 'int', 'float', 'string', 'array', 'null', 'true', 'false', 'boolean', 'mod',
                  'is', 'IS', 'not', 'and', 'or',
                  'break', 'continue', 'if', 'do', 'then', 'while', 'foreach', 'match', 'case', 'end',
                  'function', 'return', 'returns')

block_statements = ('if', 'foreach', 'while', 'match', 'function')

punctuation = (';', ':', ',',
               '[', ']', '{', '}', '(', ')',
               ':=', '=',
               '=>', '->',
               '+', '-', '*', '**', '/', '//', '%', '++', '--', 
               '~', '&', '|', '>>', '<<',
               '<', '<=', '>', '>=', '==', '!=' , '+=')

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
   '--' : 'MINUS_MINUS',
   '->' : 'RETURN_TYPE_ARROW'
}

followers = ('=', '>', '<', '+', '*', '-')

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
        self.indent_level = 0 # how many indents currently
        self.dents_list: list[Token] = [] # stores indents and dedents
        self.checked_indent = False
        self.lines: dict[int, dict] = {}
        self.last_line_break_index = 0

    def __len__(self):
        return len(self.tokens_list)

    def __getitem__(self, key) -> Token:
        return self.tokens_list[key]

    def pos(self):
        return Pos(self.idx, self.col, self.ln)

    def current_line(self) -> str:
        try:
            current_line = self.lines[self.ln]['value']
        except KeyError:
            # we haven't yet added current line
            begin = self.last_line_break_index + 1
            if self.text[self.idx] == '\n':
                end = self.idx
            else:
                end = self.text.find('\n', self.idx+1)
            current_line = self.text[begin:end]
            self.lines[self.ln] = {'value': current_line, 'pos': (begin, end)}
        return current_line

    def advance(self, steps):
        self.idx += steps
        if self.idx < len(self.text):
            self.current_char = self.text[self.idx]
        else:
            self.current_char = ''
        if steps == 1 and self.text[self.idx - 1] == '\n':
            self.last_line_break_index = self.idx - 1
            self.checked_indent = False
            self.col = 0
            self.ln += 1
        else:
            self.col += steps
        return self

    def next_token(self) -> tuple[Token | None, str | None]:
        token = None
        steps = 1
        if self.current_char != '': # it is not EOF
            if self.current_char == '\n':
                # NEWLINE
                token = Token(name='NEWLINE', value='\n', pos_begin=self.pos())
                token.pos_end = Pos(token.pos_begin.idx+1, token.pos_begin.col+1, self.ln)
                steps = 1

            # self.current_char == '#' 
            elif self.current_char == '#':
                # COMMENT
                next_new_line = self.text.find('\n', self.idx) # NEWLINE is the only thing that stops a comment
                token = Token(name='COMMENT')
                token.pos_begin = self.pos()
                if next_new_line != -1:
                    # this comment is not in last line
                    token.value = self.text[self.idx:next_new_line]
                else:
                    # this comment is in last line
                    token.value = self.text[self.idx:]
                token.pos_end = Pos(token.pos_begin.idx+len(token.value), token.pos_begin.col+len(token.value), self.ln)
                steps = len(token.value)

            elif string := string_pattern.match(string=self.text, pos=self.idx):
                # STRING
                match_value = string.group()
                token = Token(value=match_value)
                if self.tokens_list[-1].value == 'end':
                    # this line is like: end "some text here"
                    token.name = "END_LABEL"
                else:
                    token.name = 'F-STRING' if match_value[0] == 'f' else 'STRING'
                token.pos_begin = begin = self.pos()
                token.pos_end = Pos(begin.idx+len(token.value), begin.col+len(token.value), begin.ln)
                steps = len(token.value)

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
                
                token = Token()
                token.pos_begin = begin = self.pos()
                token.value = current_identifier
                token.pos_end = Pos(begin.idx+len(token.value), begin.idx+len(token.value), self.ln)
                
                if token.value in language_words:
                    token.name = 'KEYWORD'
                else:
                    if current_identifier in self.identifiers_table:
                        # we met this identifier before
                        token.name = self.identifiers_table[token.value][-1].name
                        self.identifiers_table[token.value].append(token)
                    else:
                        # A new identifier
                        token.name = 'NAME'
                        self.identifiers_table[token.value] = [token]
                steps = len(token.value)

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
                    if self.tokens_list[-1].name == 'CONST_NAME' and token.value == '=':
                        # Constant re-assignment, illegal
                        error = f'Line {self.ln + 1}:\n'
                        error += 'Constant re-assignment error:\n' + self.current_line() + '\n' + (' ' * self.col)
                        const_name_token = self.tokens_list[-1]
                        error += '^\n' + (' ' * self.col) + f'Constant ({const_name_token.value}) re-assignment\n'
                        const_declaration_line = self.identifiers_table[const_name_token.value][0].pos_begin.ln
                        error += f'Defined here, line {const_declaration_line + 1}:\n'
                        error += self.lines[const_declaration_line]['value']
                        return None, error
                
                token.name = punctuation_dict[token.value]
                token.pos_end = Pos(begin.idx+len(token.value), begin.col+len(token.value), self.ln)
                steps = len(token.value)

            elif number_match := number_pattern.match(string=self.text, pos=self.idx):
                # A NUMBER
                match_value = number_match.group()
                begin =   self.pos()
                token =   Token(name='NUMBER', pos_begin=begin)
                if int_pattern.match(string=match_value):
                    # int
                    token.value = int(match_value)
                else:
                    # float
                    token.value = float(match_value)
                end=Pos(token.pos_begin.idx+len(str(token.value)), token.pos_begin.col+len(str(token.value)), self.ln)
                token.pos_end = end
                steps = len(str(token.value)) # since token.value is a number, type-casted in lines 267=>272
        self.advance(steps)
        if token is not None:
            # we have a valid token
            self.tokens_list.append(token)
        return token, None

    def __iter__(self):
        while True:
            token, error = None, None
            if self.col == 0 and not self.checked_indent:
                # Check for indentation
                current_line = self.current_line()
                self.checked_indent = True
                current_line_line_break = self.idx
                if self.text[self.idx] != '\n':
                    current_line_line_break = self.text.find('\n', self.idx)
                if current_line_line_break == -1:
                    # this is last line
                    current_line_line_break = len(self.text)
                if len(current_line) == 0 or re.fullmatch(pattern=r'\s+', string=current_line):
                    # this line is empty or it is just whitespaces
                    self.idx = current_line_line_break
                    self.col += len(current_line)
                    self.current_char = '\n'
                    continue
                else:
                    # this line contains some non-whitespaces
                    first_non_white_space = re.compile(r'[^\s]').search(self.text, pos=self.idx, endpos=current_line_line_break)
                    first_non_white_space = first_non_white_space.start()
                    captured_indent = self.text[self.idx:first_non_white_space]
                    captured_indent = captured_indent.replace('\t', ' ' * 4)
                    error = ''
                    if len(captured_indent) % 4 != 0:
                        # Syntax Error: Indentation must a multiple of 4
                        error += f'In line {self.ln + 1}, you have a Syntax Error: Indentation must be a multiple of 4\n'
                        error += self.current_line() + '\n'
                        error += '^' * len(captured_indent) + f' Indent of {len(captured_indent)} spaces'
                    current_level = len(captured_indent) // 4
                    if self.indent_level != current_level:
                        if ' ' in captured_indent and '\t' in captured_indent:
                            # Syntax Error: Mixing spaces and tabs in indentation
                            error += f'Line {self.ln + 1}:\n'
                            error += current_line + '\n'
                            error += '^' * len(captured_indent) + '\n'
                            error += 'Syntax Error: Mixing spaces and tabs in indentation'
                        if self.ln == 0 and len(captured_indent) != 0:
                            # if it is first line, this is Syntax Error
                            if len(error) == 0:
                                error += 'Line 1:\n'
                                error += current_line + '\n'
                                error += '^' * len(captured_indent) + '\n'
                            error += 'Syntax Error: Indenting first line'
                        if error == '':
                            # this is not first line
                            # Dont add Indent/Dedent token only if current_level is not 0
                            begin = self.pos()
                            token = Token(value=captured_indent, pos_begin=begin)
                            token.pos_end = Pos(begin.idx+len(captured_indent), begin.col+len(captured_indent), self.ln)
                            if current_level < self.indent_level:
                                # DEDENT
                                self.indent_level -= 1
                                token.name = 'DEDENT'
                            elif self.indent_level < current_level:
                                # INDENT
                                self.indent_level += 1
                                token.name = 'INDENT'
                            self.idx = first_non_white_space
                            self.col = current_line.find(self.text[first_non_white_space])
                            if self.idx < len(self.text):
                                self.current_char = self.text[self.idx]
                            else:
                                self.current_char = ''
                            self.tokens_list.append(token)
                            self.dents_list.append(token)
                        else:
                            self.checked_indent = False
                        
                    if error == '':
                        error = None
            else:
                token, error = self.next_token()
            #
            #
            if error is not None:
                print('\nError:\n' + error)
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
        source = str(source_file.read()) + '\n'
        tokenizer = Tokenizer(source)
        for t in tokenizer:
            print(t)
else:
    source = """
int x := 123;
function f(const int x) -> int => {

    return x;

}

"""
    tokenizer = Tokenizer(source)
    for t in tokenizer:
        print(t)
    print(tokenizer.contexts_list)
