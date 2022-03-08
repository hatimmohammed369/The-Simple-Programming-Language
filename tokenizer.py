#!/usr/local/bin/python3.10

import re
from typing import Any, Union
from dataclasses import dataclass
from const import *

####################################################################################################

# Tokenizer: takes texts and turns it into "words" (tokens)


@dataclass(init=True, repr=True)
class Line:
    value: str = ""
    begin: int = 0
    end: int = 0


@dataclass(init=True, eq=True, repr=True)
class Pos:
    idx: int = 0
    col: int = 0
    ln: int = 0


@dataclass(init=True, repr=True, eq=True)
class Token:
    name: str = ""
    value: Any = object()
    begin: Pos = Pos()
    end: Pos = Pos()

    def __repr__(self):
        self_idx = f"{self.begin.idx}-{self.end.idx}"
        self_col = f"{self.begin.col}-{self.end.col}"
        return f"Token({self.name}, {repr(self.value)}, ({self_idx}, {self_col}, {self.begin.ln}))"

    __str__ = __repr__


class Tokenizer:
    def __init__(self, text: str):
        self.text: str = text
        self.current_char: str = ""
        self.idx, self.ln, self.col = 0, 0, 0
        if len(text) != 0:
            self.current_char = self.text[0]
        self.tokens_list: list[Token] = []
        self.identifiers_table: dict[str, list[Token]] = {}
        self.indent_stack = [0]  # how many indents currently
        self.checked_indent = False
        self.lines: dict[int, Line] = {}
        self.last_line_break_index = -1
        self.done = False  # becomes True after this instance calls method tokenize()

    def pos(self):
        return Pos(self.idx, self.col, self.ln)

    def current_line(self) -> Line:
        try:
            current_line = self.lines[self.ln]
        except KeyError:
            # we haven't yet added current line
            begin = self.last_line_break_index + 1
            if self.text[self.idx] == "\n":
                end = self.idx
            else:
                end = self.text.find("\n", self.idx + 1)
                if end == -1:
                    # since we're using str.find, -1 is a possible output
                    end = len(self.text)
            current_line = self.lines[self.ln] = Line(self.text[begin:end], begin, end)
        return current_line

    def advance(self, steps):
        self.idx += steps
        if self.idx < len(self.text):
            self.current_char = self.text[self.idx]
        else:
            self.current_char = ""
        if steps == 1 and self.text[self.idx - 1] == "\n":
            self.last_line_break_index = self.idx - 1
            self.checked_indent = False
            self.col = 0
            self.ln += 1
        else:
            self.col += steps
        return self

    def next_token(self) -> Union[Token, None]:
        token = None
        steps = 1
        if self.current_char != "":  # it is not EOF
            if self.current_char == "\n":
                # LINE_BREAK
                token = Token(name="LINE_BREAK", value="\n", begin=self.pos())
                token.end = Pos(token.begin.idx + 1, token.begin.col + 1, self.ln)
                steps = 1

            # self.current_char == '#'
            elif self.current_char == "#":
                # COMMENT
                next_new_line = self.text.find(
                    "\n", self.idx
                )  # LINE_BREAK is the only thing that stops a comment
                token = Token(name="COMMENT")
                token.begin = self.pos()
                if next_new_line != -1:
                    # this comment is not in last line
                    token.value = self.text[self.idx : next_new_line]
                else:
                    # this comment is in last line
                    token.value = self.text[self.idx :]
                token.end = Pos(
                    token.begin.idx + len(token.value),
                    token.begin.col + len(token.value),
                    self.ln,
                )
                steps = len(token.value)

            elif string := STRING_PATTERN.match(string=self.text, pos=self.idx):
                # STRING
                match_value = string.group()
                token = Token(value=match_value)
                if self.tokens_list[-1].value == "end":
                    # this line is like: end "some text here"
                    token.name = "END_LABEL"
                token.begin = begin = self.pos()
                token.end = Pos(
                    begin.idx + len(token.value), begin.col + len(token.value), begin.ln
                )
                steps = len(token.value)

            elif name := NAME_PATTERN.match(string=self.text, pos=self.idx):
                # IDENTIFIER
                # an identifier or a keyword
                current_identifier = name.group()
                token = Token()
                token.begin = begin = self.pos()
                token.value = current_identifier
                token.end = Pos(
                    begin.idx + len(token.value), begin.col + len(token.value), self.ln
                )

                if token.value in KEYWORDS:
                    if token.value in ('not', 'and', 'or'):
                        token.name = 'OPERATOR'
                    else:
                        token.name = "KEYWORD"
                else:
                    token.name = "NAME"
                steps = len(token.value)

            elif op := OPERATOR_PATTERN.match(string=self.text, pos=self.idx):
                # ALL SORTS OF OPERATORS
                begin = self.pos()
                token = Token(begin=begin)
                token.name = 'OPERATOR'
                token.value = op.group()

                token.end = Pos(
                    begin.idx + len(token.value), begin.col + len(token.value), self.ln
                )
                steps = len(token.value)

            elif sep := SEPARATOR_PATTERN.match(string=self.text, pos=self.idx):
                #(, ), {, }, :, (,), ;
                begin = self.pos()
                token = Token(begin=begin)
                token.name = "SEPARATOR"
                token.value = sep.group()

                token.end = Pos(
                    begin.idx + len(token.value), begin.col + len(token.value), self.ln
                )
                steps = len(token.value)

            elif number_match := NUMBER_PATTERN.match(string=self.text, pos=self.idx):
                # A NUMBER
                match_value = number_match.group()
                begin = self.pos()
                token = Token(name="NUMBER", begin=begin)
                token.value = match_value
                if INT_PATTERN.match(string=match_value):
                    # int
                    token.name = "INT_" + token.name
                else:
                    # float
                    token.name = "FLOAT_" + token.name
                end = Pos(
                    token.begin.idx + len(str(token.value)),
                    token.begin.col + len(str(token.value)),
                    self.ln,
                )
                token.end = end
                steps = len(
                    str(token.value)
                )  # since token.value is a number, type-casted in lines 267=>272
        self.advance(steps)
        if token is not None:
            # we have a valid token
            self.tokens_list.append(token)
        return token

    def tokenize(self):
        while self.current_char != "":
            token, error = None, None
            if self.col == 0 and not self.checked_indent:
                # Check for indentation
                self.checked_indent = True
                current_line_object = self.current_line()
                current_line = current_line_object.value
                current_line_line_break = current_line_object.end
                # VERY IMPORTANT NOTICE
                # When we encounter a \n during tokenization, we consider this \n as the end of some line
                # namely, the all characters preceding this \n up to the nearest \n but excluding it
                #
                # More clearly, when we encounter a line break (\n) called X
                # X is considered at the (END) of some line, after all this \n character is called (Line Break)
                # So we search backwards until we hit Y, which is file begin or another \n
                # so X's line is all characters between Y and X
                # and of course excluding both X and Y because we don't want \n in line representation

                first_non_white_space = re.compile(r"[^\s]").search(
                    string=self.text, pos=self.idx, endpos=current_line_line_break
                )
                if first_non_white_space is None:
                    # this line is empty or it is just whitespaces
                    self.idx = current_line_line_break
                    self.col += len(current_line)
                    self.current_char = "\n"
                    continue
                else:
                    # this line contains some non-whitespaces
                    first_non_white_space = first_non_white_space.start()
                    captured_indent = self.text[self.idx : first_non_white_space]
                    captured_indent = captured_indent.replace("\t", " " * 4)
                    error = ""

                    # Error Handling
                    if len(captured_indent) % 4 != 0:
                        # Syntax Error: Indentation must a multiple of 4
                        error += f"In line {self.ln + 1}, you have a Syntax Error: Indentation must be a multiple of 4\n"
                        error += current_line + "\n"
                        error += (
                            "^" * len(captured_indent)
                            + f" Indent of {len(captured_indent)} spaces"
                        )
                    captured_indent_level = len(captured_indent) // 4
                    if " " in captured_indent and "\t" in captured_indent:
                        # Syntax Error: Mixing spaces and tabs in indentation
                        error += f"Line {self.ln + 1}:\n"
                        error += current_line + "\n"
                        error += "^" * len(captured_indent) + "\n"
                        error += "Syntax Error: Mixing spaces and tabs in indentation"
                    if self.ln == 0 and len(captured_indent) != 0:
                        # if it is first line, this is Syntax Error
                        if len(error) == 0:
                            error += "Line 1:\n"
                            error += current_line + "\n"
                            error += "^" * len(captured_indent) + "\n"
                        error += "Syntax Error: Indenting first line"
                    # Error Handling Done!

                    if error == "":
                        # this is not first line
                        # Dont add Indent/Outdent token only if captured_indent_level is not 0
                        current_indent_level = self.indent_stack[-1]

                        begin = self.pos()
                        token = Token(value=captured_indent, begin=begin)
                        token.end = Pos(
                            begin.idx + len(captured_indent),
                            begin.col + len(captured_indent),
                            self.ln,
                        )
                        if captured_indent_level < current_indent_level:
                            # OUTDENT
                            self.indent_stack.pop(-1)
                            token.name = "OUTDENT"
                        elif current_indent_level < captured_indent_level:
                            # INDENT
                            self.indent_stack.append(captured_indent_level)
                            token.name = "INDENT"
                        else:
                            # no indent or outdent, make token None
                            token = None
                        self.idx = first_non_white_space
                        self.col = current_line.find(self.text[first_non_white_space])
                        if self.idx < len(self.text):
                            self.current_char = self.text[self.idx]
                        else:
                            self.current_char = ""
                        if token is not None:
                            # dont add indent/outdent token if it has no name, this means there's no indent or outdent
                            self.tokens_list.append(token)

                    if error == "":
                        error = None
            else:
                self.next_token()
            #
            #
            if error is not None:
                print("\nError:\n" + error)
                exit(0)
        # end "while self.current_char != "" "
        self.done = True
        return self

    def __iter__(self):
        if self.done is False:
            self.tokenize()
        return iter(self.tokens_list)
