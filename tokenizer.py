#!/usr/local/bin/python3.10

import re
from typing import Any, Tuple, List
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


@dataclass(init=True, repr=True, eq=True)
class Block:
    header: Token = Token()
    allowed_indent: int = 0


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
        supplied_spaces_explicitly=False,  # Did you supply --spaces explicitly?
    ):
        self.text: str = text
        self.current_char: str = ""
        self.idx, self.ln, self.col = 0, 0, 0
        if len(text) != 0:
            self.current_char = self.text[0]
        self.tokens_list: list[Token] = []
        self.indent_stack = [0]  # how many indents currently
        self.checked_indent = False
        self.lines: dict[int, Line] = {}
        self.last_line_break_index = -1

        self.indent_type: str = indent_type.lower()
        if self.indent_type not in (" ", "\t"):
            raise ValueError(f'{self.indent_type = } must be either " " or "\\t"')

        self.indent_size = indent_size

        self.done = (
            False  # becomes True after this instance successfully executes tokenize()
        )

        self.supplied_spaces_explicitly = supplied_spaces_explicitly

        self.left_parenthesis_stack = (
            []
        )  # Store left parentheses "( or [" tokens to enable multi-line statements

        self.blocks: List[Block] = []

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

    def next_token(self) -> Tuple[str, Token]:
        error, token = "", None
        steps = 1
        indent_name = "space" if self.indent_type == " " else "tab"
        if (
            self.col == 0  # It's line head
            and not self.checked_indent  # We have not check indentation of this line
            and len(self.left_parenthesis_stack)
            == 0  # this is a not a multi-line statement
        ):
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
                return "", None  # JUST IGNORE THIS TYPE-CHECKING ERROR
            elif (
                len(self.blocks) > 0
                or current_line[0]
                in (
                    " ",
                    "\t",
                )
                and first_non_white_space.group()
                not in (
                    "#",
                    ",",
                    ";",
                    ":",
                    "(",
                    ")",
                    "[",
                    "]",
                    '"',
                )
            ):  # Do not check indentation these separators
                # this line starts with a space or tab
                # so that we don't walk down this bunch of code only returning token=None
                # when we have no indentation or indenation has not changed
                # this line contains some non-whitespaces
                first_non_white_space = first_non_white_space.start()
                captured_indent = self.text[self.idx : first_non_white_space]

                # <======================================================================>
                # Error Handling
                opposite_indent_name = "tab" if indent_name == "space" else "space"

                # <======================================================================>
                # Indenting top level code error
                indenting_top_level_code = False
                if (
                    len(self.left_parenthesis_stack) == 0  # (Multi-line)ing is disable
                    and len(self.blocks)
                    == 0  # No active blocks, we are inside no block, we livin' in top level code
                    # So no active () and no active blocks
                ) and len(
                    captured_indent
                ) != 0:  # Trying to add an actual indent
                    # Indentation Error: Indenting top-level code
                    error += f"Indentation Error in line {self.ln + 1}: Indenting top-level code:\n"
                    error += " " * 4
                    for c in captured_indent:
                        error += "+" if c == " " else "*"
                    error += current_line[len(captured_indent) :] + "\n"
                    error += " " * 4 + "^" * len(captured_indent) + "\n"
                    error += " " * 4 + "Found indentation, remove it\n"
                    indenting_top_level_code = True

                if indenting_top_level_code:
                    # No need to see other errors
                    return error, None  # JUST IGNORE THIS TYPE-CHECKING ERROR
                # Indenting top level code error
                # <======================================================================>

                # First check this captured_indent is matches self.indent_type
                opposite_type_detected = False
                if (
                    (
                        "\t" in captured_indent and indent_name == "space"
                    )  # Using tabs when indenting with spaces
                    or (
                        " " in captured_indent and indent_name == "tab"
                    )  # Using spaces when indenting with tabs
                ) and self.ln != 0:  # since indentation in first line is allowed in the first place
                    error += f"Indentation Error: Using (disabled) {opposite_indent_name}s with (enabled) {indent_name}s indentation\n"
                    error += f"Line {self.ln + 1}:\n"
                    error += "    "
                    for c in captured_indent:
                        error += "+" if c == " " else "*"
                    error += current_line[len(captured_indent) :] + "\n"
                    error += "    "
                    illegal_chars = 0
                    for c in captured_indent:
                        if c != self.indent_type:
                            error += "^"
                            illegal_chars += 1
                        else:
                            error += " "
                    error += "\n"
                    error += (
                        "    "
                        + f"Found {'one' if illegal_chars == 1 else illegal_chars} "
                    )
                    error += f"{opposite_indent_name}{'s' * int(illegal_chars != 1)}\n"
                    error += f"In every INDENT in this file, remove ALL {opposite_indent_name.upper()}S\n"
                    opposite_type_detected = True

                LOWER = self.indent_size * (len(captured_indent) // self.indent_size)
                if (
                    0 < len(captured_indent[LOWER:]) < self.indent_size
                    and not opposite_type_detected
                ):
                    if error != "":
                        error += "<======================================================================>\n"
                    error += f"Indentation Error: Indenting with less than "
                    error += f"{'one' if self.indent_size == 1 else self.indent_size} "
                    error += f"{indent_name}{'s' * int(self.indent_size != 1)}\n"
                    error += " " * 4
                    error += ("+" if indent_name == "space" else "*") * len(
                        captured_indent[LOWER:]
                    )
                    error += " " + current_line[len(captured_indent) :] + "\n"
                    error += " " * 4 + " " * len(captured_indent[LOWER:])
                    error += "^"
                    error += "\n"
                    error += " " * 4
                    error += f"Found {'one' if len(captured_indent[LOWER:]) == 1 else len(captured_indent[LOWER:])} "
                    error += f"{indent_name}{'' if len(captured_indent[LOWER:]) == 1 else 's'}, "
                    needed = self.indent_size - len(captured_indent[LOWER:])
                    error += f"add {'one' if needed == 1 else needed} more {indent_name}{'' if needed == 1 else 's'}"

                # Error Handling Done
                # <======================================================================>

                if error == "":
                    # No errors
                    # Dont add Indent/Outdent token only if captured_indent_level is not 0
                    current_indent_level = self.indent_stack[-1]

                    begin = self.pos()
                    token = Token(value=captured_indent, begin=begin)
                    token.end = Pos(
                        begin.idx + len(captured_indent),
                        begin.col + len(captured_indent),
                        self.ln,
                    )
                    if len(captured_indent) < current_indent_level:
                        # OUTDENT
                        self.indent_stack.pop(-1)
                        token.name = "OUTDENT"
                        self.blocks.pop(-1)
                    elif current_indent_level < len(captured_indent):
                        # INDENT
                        self.indent_stack.append(
                            len(captured_indent)
                        )  # Use captured_indent length to 0, 4, 8, 12, ... (indent_size 4)
                        token.name = "INDENT"
                    else:
                        # no indent or outdent, make token None
                        token = None
                    steps = len(captured_indent)
            else:
                return "", None  # JUST IGNORE THIS TYPE-CHECKING ERROR

        elif self.current_char == "\n":
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
                    if token.value in BLOCK_STATEMENTS:
                        self.blocks.append(
                            Block(
                                token,
                                allowed_indent=self.indent_stack[-1] + self.indent_size,
                            )
                        )
            else:
                token.name = "NAME"
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
            steps = len(str(token.value))

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
            # ()[],;:
            if (sep.group() == ")" or sep.group() == "]") and len(
                self.left_parenthesis_stack
            ) == 0:
                cur_line_obj = self.current_line()
                current_line = cur_line_obj.value
                first_non_white_space = (
                    re.compile(r"[^\s]").match(string=current_line).start()
                )
                error += (
                    f"Syntax Error in line {self.ln + 1}: Unexpected {sep.group()}\n"
                )
                error += " " * 4 + "".join(
                    "+" if c == " " else "*"
                    for c in current_line[:first_non_white_space]
                )
                error += current_line[first_non_white_space:] + "\n"
                error += " " * 4 + " " * self.col + "^" + "\n"
                error += (
                    " " * 4
                    + " " * self.col
                    + f"This {sep.group()} has no matching {'(' if sep.group() == ')' else '['}\n"
                )
            else:
                begin = self.pos()
                token = Token(begin=begin)
                token.name = "SEPARATOR"
                token.value = sep.group()

                token.end = Pos(
                    begin.idx + len(token.value),
                    begin.col + len(token.value),
                    self.ln,
                )

                if token.value in ("(", "["):
                    # PUSH NEW MULTI-LINE STATEMENT STATE
                    self.left_parenthesis_stack.append(token)
                elif token.value in (")", "]"):
                    # POP CURRENT MULTI-LINE STATEMENT STATE
                    self.left_parenthesis_stack.pop(-1)

                steps = len(token.value)

        if error == "":  # If no errors found, then advance
            # No need to advance with errors
            self.advance(steps)
        else:
            # If errors found, add tips

            # <======================================================================>
            # Add explanatory tips
            tips = ""
            if (
                self.supplied_spaces_explicitly is False and self.indent_type != "\t"
            ):  # no --tabs or --spaces, so use --spaces by default
                tips += "You used neither --spaces not --tabs, so --spaces is used by default"
            else:
                tips += f"You used --{indent_name}s"

            tips += "\n"

            tips += (
                f"Indent type: {indent_name.title()}s\n"
                + f"Indent Size: {'One' if self.indent_size == 1 else self.indent_size} "
                + f"{indent_name.title()}{'' if self.indent_size == 1 else 's'}\n"
                + f"+ = one space | * = one tab\n"
            )
            # TIP DONE
            # <======================================================================>

            tips += "<======================================================================>\n"
            error = tips + error

        return error, token  # JUST IGNORE THIS TYPE-CHECKING ERROR

    def tokenize(self):
        while self.current_char != "":
            error, token = self.next_token()
            if error != "":
                print(error)
                exit(0)

            if token is not None:
                # we have a valid token
                self.tokens_list.append(token)
        # end "while self.current_char != "" "
        self.done = True
        return self

    def __iter__(self):
        if self.done is False:
            self.tokenize()
        return iter(self.tokens_list)


if __name__ == "__main__":
    from argparse import ArgumentParser
    from sys import argv

    parser = ArgumentParser()

    parser.add_argument("--source", help="A small code sample to execute")
    parser.add_argument("--file", help="Source file")
    parser.add_argument(
        "--spaces",
        help="Use spaces for indentation, default\n"
        + "In other words, when supplying neither --spaces not --tabs, --spaces is default",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--tabs", help="Use tabs for indentation", action="store_true", default=False
    )
    parser.add_argument(
        "--indent_size", help="Indent size", default=4
    )  # this means one indent token equals 4 spaces/tabs

    args = parser.parse_args()
    cmd_line = "".join(argv)

    # Source code
    if args.file:
        source = open(args.file).read()
    else:
        source = args.source

    # Indent type
    if (
        "--spaces" in argv and "--tabs" in argv
    ):  # both --spaces and --tabs were supplied
        print("You can not use both tabs and spaces indentation, pick one")
        exit(1)

    supplied_spaces_explicitly = False
    if (
        "--spaces" in argv and "--tabs" not in argv
    ):  # --spaces was supplied, --tabs was not
        indent = " "
        supplied_spaces_explicitly = True
    elif (
        "--tabs" in argv and "--spaces" not in argv
    ):  # --tabs was supplied, --spaces was not
        indent = "\t"
        supplied_spaces_explicitly = False
    else:  # neither --spaces nor --tabs, then assume --spaces
        indent = " "  # not supplied
        supplied_spaces_explicitly = False

    # Indent size
    try:
        args.indent_size = int(args.indent_size)
    except:
        print(f"--indent_size '{args.indent_size}' is not a valid positive integer")
        exit(0)

    if args.indent_size <= 0:
        print(f"--indent_size '{args.indent_size}' is not a positive integer")
        exit(0)

    if "--indent_size" in argv:  # --indent_size was supplied, use supplied value
        size = args.indent_size
    else:
        # --indent_size was NOT supplied
        if "--tabs" in argv:  # --tabs only
            size = 1  # Use 1 tab
        else:  # --spaces or (no --spaces and no --tabs)
            size = 4

    if size <= 0:
        print("Please give --indent_size a positive number")
        exit(0)

    tokenizer = Tokenizer(
        text=source,
        indent_type=indent,
        indent_size=size,
        supplied_spaces_explicitly=supplied_spaces_explicitly,
    )
    for token in tokenizer:
        print(token)
