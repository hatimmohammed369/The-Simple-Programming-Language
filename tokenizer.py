#!/usr/local/bin/python3.10

import re
from typing import Any
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


class Tokenizer_Result(Result):
    def __init__(self, error_msg: str = "", token: Token = Token()):
        super().__init__()
        self.error_msg: str = error_msg
        self.result: Token = token


class Tokenizer:
    def __init__(
        self,
        text: str,  # Text to be tokenized
        indent_type=" ",  # which character to use for indentation,
        # if indent_type.lower() == "s" then we use spaces for indentation
        # if indent_type.lower() == "t" then we use tabs for indentation
        indent_size=4,  # How many indent characters in a single indent token
        tab_size=4,  # How many spaces in a single tab
    ):
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

        self.indent_type: str = indent_type.lower()
        if self.indent_type not in (" ", "\t"):
            raise ValueError(f'{self.indent_type} must be either " " or "\\t"')
        self.indent_size = indent_size
        self.tab_size = tab_size

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

    def next_token(self) -> Token:
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
                    if token.value in ("not", "and", "or"):
                        token.name = "OPERATOR"
                    else:
                        token.name = "KEYWORD"
                else:
                    token.name = "NAME"
                steps = len(token.value)

            elif op := OPERATOR_PATTERN.match(string=self.text, pos=self.idx):
                # ALL SORTS OF OPERATORS
                begin = self.pos()
                token = Token(begin=begin)
                token.name = "OPERATOR"
                token.value = op.group()

                token.end = Pos(
                    begin.idx + len(token.value), begin.col + len(token.value), self.ln
                )
                steps = len(token.value)

            elif sep := SEPARATOR_PATTERN.match(string=self.text, pos=self.idx):
                # (, ), {, }, :, (,), ;
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
                    error = ""

                    # Error Handling

                    # Make sure this indentation is spaces only to tabs only not a mix of spaces and tabs
                    if (
                        " " in captured_indent
                        and "\t" in captured_indent
                        and self.ln != 0
                    ):
                        # Syntax Error: Mixing spaces and tabs in indentation
                        error += f"Syntax Error in line {self.ln + 1}: Mixing spaces and tabs in indentation\n"

                        error += "\n"
                        for c in captured_indent:
                            if c == "\t":
                                error += "+" * self.tab_size
                            else:
                                error += "*"
                        error += current_line[len(captured_indent) :] + "\n"

                    if error:
                        # Add explanatory tips
                        indent_name = "Spaces" if self.indent_type == " " else "Tabs"
                        tips = (
                            f"Indent type: {indent_name}\n"
                            + f"Indent Size: {self.indent_size} {indent_name}\n"
                            + f"Tab Size:    {self.tab_size} Spaces\n"
                            + f"+ = one space | * = one tab | "
                            + f"{'+' * self.tab_size} = one tab converted to spaces ({self.tab_size} {indent_name})\n"
                        )
                        tips += "<======================================================================>\n"
                        error = tips + error

                    # This line below must be here, because replacing all tabs with (self.tab_size) spaces
                    # will never trigger above if which reports mixing tabs and spaces
                    captured_indent = captured_indent.replace("\t", " " * self.tab_size)

                    # Make sure this indentation is uniform
                    if len(captured_indent) % self.indent_size != 0 and self.ln != 0:
                        # Syntax Error: Indentation must a multiple of (self.indent_size)
                        error += "<======================================================================>"
                        error += "\n"

                        error += f"Syntax Error in line {self.ln + 1}: Indentation must be a multiple of {self.indent_size}"
                        error += "\n\n"

                        error += ("+" if self.indent_type == " " else "*") * len(
                            captured_indent.replace("\t", " " * self.tab_size)
                        )
                        error += current_line[len(captured_indent) :] + "\n\n"
                        error += f"Found indent of {len(captured_indent)} {'spaces' if self.indent_type == ' ' else 'tabs'}\n"

                    captured_indent_level = len(captured_indent) // 4
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
            else:
                self.next_token()
            #
            #
            if error:
                print(error)
                exit(0)
        # end "while self.current_char != "" "
        self.done = True
        return self

    def __iter__(self):
        if self.done is False:
            self.tokenize()
        return iter(self.tokens_list)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument("--source", help="A small code sample to execute")
    parser.add_argument("--file", help="Source file")
    parser.add_argument(
        "--spaces",
        help="Use spaces for indentation",
        action="store_true",
        default=True
    )
    parser.add_argument(
        "--tabs",
        help="Use tabs for indentation",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--indent_size", help="Indent size", default=4
    )  # this means one indent token equals 4 spaces/tabs
    parser.add_argument("--tab_size", help="Tab size in spaces", default=4)

    args = parser.parse_args()

    # Source code
    if args.file:
        with open(args.file, "r") as source_file:
            source = str(source_file.read())
    else:
        source = args.source

    # Tab size
    if args.tab_size:
        tab = args.tab_size
    else:
        tab = 4

    # Indent type
    if args.spaces and args.tabs:
        print("You can use both tabs and spaces indentation, pick one")
        exit(1)
    elif args.spaces:
        indent = " "
    else:
        indent = "\t"

    # Indent size
    if args.indent_size:
        size = args.indent_size
    else:
        size = 4

    tokenizer = Tokenizer(
        text=source, indent_type=indent, indent_size=size, tab_size=tab
    )
    for token in tokenizer:
        print(token)
