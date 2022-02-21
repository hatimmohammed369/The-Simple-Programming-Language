#!/usr/local/bin/python3.10

import re
from typing import Any
from dataclasses import dataclass

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


data_types = ("int", "float", "string", "boolean", "array", "null")

language_words = (
    "const",
    "int",
    "float",
    "string",
    "array",
    "null",
    "true",
    "false",
    "boolean",
    "mod",
    "is",
    "IS",
    "not",
    "and",
    "or",
    "break",
    "continue",
    "if",
    "do",
    "then",
    "while",
    "foreach",
    "match",
    "case",
    "end",
    "function",
    "return",
    "returns",
)

block_statements = ("if", "foreach", "while", "match", "function")

punctuation = (
    ";",
    ":",
    ",",
    "[",
    "]",
    "{",
    "}",
    "(",
    ")",
    ":=",
    "=",
    "=>",
    "->",
    "+",
    "-",
    "*",
    "**",
    "/",
    "//",
    "%",
    "++",
    "--",
    "~",
    "&",
    "|",
    ">>",
    "<<",
    "<",
    "<=",
    ">",
    ">=",
    "==",
    "!=",
    "+=",
)

punctuation_dict = {
    ";": "SEMICOLON",
    ":": "COLON",
    ",": "COMMA",
    "[": "LEFT_SQUARE_BRACKET",
    "]": "RIGHT_SQUARE_BRACKET",
    "{": "LEFT_CURLY_BRACE",
    "}": "RIGHT_CURLY_BRACE",
    "(": "LEFT_PARENTHESES",
    ")": "RIGHT_PARENTHESES",
    ":=": "COLON_EQUAL",
    "=": "EQUAL",
    "=>": "RETURN_ARROW",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "**": "DOUBLE_STAR",
    "/": "SLASH",
    "//": "DOUBLE_SLASH",
    "%": "PERCENT",
    "~": "NOT",
    "&": "AND",
    "|": "OR",
    ">>": "RIGHT_SHIFT",
    "<<": "LEFT_SHIFT",
    "<": "LESS",
    "<=": "LESS_EQUAL",
    ">": "GREATER",
    ">=": "GREATER_EQUAL",
    "==": "EQUAL_EQUAL",
    "!=": "NOT_EQUAL",
    "+=": "PLUS_EQUAL",
    "++": "PLUS_PLUS",
    "--": "MINUS_MINUS",
    "->": "RETURN_TYPE_ARROW",
}

followers = ("=", ">", "<", "+", "*", "-")

int_pattern = re.compile(r"[+-]{0,1}\d+([eE][+-]{0,1}\d+){0,1}")
float_pattern = re.compile(
    r"[+-]{0,1}\d+[.]\d*([eE][+-]{0,1}\d+){0,1}|[+-]{0,1}\d*[.]\d+([eE][+-]{0,1}\d+){0,1}"
)
number_pattern = re.compile(float_pattern.pattern + "|" + int_pattern.pattern)
string_pattern = re.compile(r'f{0,1}".*?(?<!\\)"')
indent_pattern = re.compile(r"[ ]{4}|[\t]")  # 4 consecutive spaces or a single tab
name_pattern = re.compile(r"[_a-zA-Z][_a-zA-Z0-9]*")


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

    def next_token(self) -> tuple[Token | None, str | None]:
        token = None
        steps = 1
        if self.current_char != "":  # it is not EOF
            if self.current_char == "\n":
                # NEWLINE
                token = Token(name="NEWLINE", value="\n", begin=self.pos())
                token.end = Pos(token.begin.idx + 1, token.begin.col + 1, self.ln)
                steps = 1

            # self.current_char == '#'
            elif self.current_char == "#":
                # COMMENT
                next_new_line = self.text.find(
                    "\n", self.idx
                )  # NEWLINE is the only thing that stops a comment
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

            elif string := string_pattern.match(string=self.text, pos=self.idx):
                # STRING
                match_value = string.group()
                token = Token(value=match_value)
                if self.tokens_list[-1].value == "end":
                    # this line is like: end "some text here"
                    token.name = "END_LABEL"
                else:
                    token.name = "F-STRING" if match_value[0] == "f" else "STRING"
                token.begin = begin = self.pos()
                token.end = Pos(
                    begin.idx + len(token.value), begin.col + len(token.value), begin.ln
                )
                steps = len(token.value)

            elif name := name_pattern.match(string=self.text, pos=self.idx):
                # IDENTIFIER
                # an identifier or a keyword
                current_identifier = name.group()
                token = Token()
                token.begin = begin = self.pos()
                token.value = current_identifier
                token.end = Pos(
                    begin.idx + len(token.value), begin.idx + len(token.value), self.ln
                )

                if token.value in language_words:
                    token.name = "KEYWORD"
                else:
                    if current_identifier in self.identifiers_table:
                        # we met this identifier before
                        token.name = self.identifiers_table[token.value][-1].name
                        self.identifiers_table[token.value].append(token)
                    else:
                        # A new identifier
                        token.name = "NAME"
                        self.identifiers_table[token.value] = [token]
                steps = len(token.value)

            elif self.current_char in punctuation:
                # SOMETHING LIKE *, +, {, %, ;, .....
                begin = self.pos()
                token = Token(begin=begin)
                if (
                    self.idx + 1 < len(self.text)
                    and self.text[self.idx + 1] in followers
                ):
                    # Things like :=, ==, !=, <=, <<
                    token.value = self.text[self.idx : self.idx + 2]
                else:
                    # Things like +, -, /, *, any thing single character
                    token.value = self.text[self.idx : self.idx + 1]

                token.name = punctuation_dict[token.value]
                token.end = Pos(
                    begin.idx + len(token.value), begin.col + len(token.value), self.ln
                )
                steps = len(token.value)

            elif number_match := number_pattern.match(string=self.text, pos=self.idx):
                # A NUMBER
                match_value = number_match.group()
                begin = self.pos()
                token = Token(name="NUMBER", begin=begin)
                if int_pattern.match(string=match_value):
                    # int
                    token.value = int(match_value)
                else:
                    # float
                    token.value = float(match_value)
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
        return token, None

    def __iter__(self):
        while True:
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
                        # Dont add Indent/Dedent token only if captured_indent_level is not 0
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
                token, error = self.next_token()
            #
            #
            if error is not None:
                print("\nError:\n" + error)
                exit(0)
            if token is not None:
                yield token
            if self.current_char == "":
                # DONE!
                break

    def tokenize(self):
        while self.current_char != "":
            self.next_token()
        return self


####################################################################################################


class Interpreter:
    def init(self, tokenizer):
        self.tokenizer = tokenizer

    def exec(self):
        for token in tokenizer:
            if token.name == "COMMENT":
                pass
        return


####################################################################################################

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument("-s", "--source", help="A small code sample to execute")
    parser.add_argument("-f", "--file", help="Source file")

    args = parser.parse_args()

    if args.file:
        with open(args.file, "r") as source_file:
            source = str(source_file.read())
    else:
        source = args.source

    tokenizer = Tokenizer(source)

    for token in tokenizer:
        print(token)
