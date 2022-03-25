#!/usr/local/bin/python3.10

from posixpath import abspath
import re
from typing import Tuple, List, Dict
from dataclasses import dataclass
from const import *
from os import path

####################################################################################################

# Tokenizer: takes texts and turns it into "words" (tokens)


@dataclass(init=True, repr=True)
class Line:
    value: str = "" # Actual text excluding \n (line breaks)
    begin: int = 0 # nearest line break when searching backwards
    end: int = 0 # nearest line break when searching forwards


@dataclass(init=True, eq=True, repr=True)
class Pos:
    idx: int = 0
    col: int = 0
    ln: int = 0


@dataclass(init=True, repr=True, eq=True)
class Token:
    name: str = ""
    value: str = ""
    begin: Pos = None
    end: Pos = None

    def __repr__(self):
        self_idx = f"{self.begin.idx}-{self.end.idx}"
        self_col = f"{self.begin.col}-{self.end.col}"
        return f"Token({self.name}, {repr(self.value)}, ({self_idx}, {self_col}, {self.begin.ln}))"

    __str__ = __repr__


class Block:
    SINGLE = "SINGLE-LINE"
    MULTI = "MULTI-LINE"
    lines_dict: Dict[int, Line] = {}

    def __init__(
        self,
        header: List[Token] =None,
        header_complete: bool =False,
        header_type: str =None,
        header_indent: Token =None,
        indent_size: int =None,
    ):
        # All tokens comprising this block's header, like (if) token and all tokens of its condition
        self.header: List[Token] = header

        self.header_name: str = self.header[0].value # holds block keyword, something like 'if', 'while', 'else'

        # True self.header has all components in a block header, False otherwise
        # say we have an (if) header, self.header must be if token and all tokens comprising the condition
        # then self.header_complete becomes True
        self.header_complete: bool = header_complete

        self.header_type: str = header_type  # "SINGLE-LINE" or "MULTI-LINE"

        self.header_indent: Token = header_indent  # Header token indent value

        self.indent_size = indent_size  # actual indent used inside this block

        self.lines: List[int] = []
        for tok in self.header:
            if tok.begin.ln not in self.lines:
                self.lines.append(tok.begin.ln)

        self.header_string: str = None # the whole block header but as string
        # not to be confused with header
        # header is a list holding all tokens comprising this block's header
        # header_string takes some tokens in (header) list and turns then into the actual piece of code, a string
        self.make_header() # computes header_string

    def make_header(self):
        if not self.header_string:
            self.header_string = "\n".join(
                Block.lines_dict[ln_idx].value
                for ln_idx in self.lines
            ) + "\n"
        return self.header_string

    def add(self, new_token: Token): # add new token
        # make sure self.header is not yet complete
        # this new_token is actually "new"
        # and DO NOT ADD line breaks
        if (
            self.header_complete is False
            and new_token not in self.header
            and new_token.begin.ln not in self.lines
            and new_token.value != "\n"
        ):
            self.header.append(new_token)
        return self

    def __repr__(self):
        return (
            "Block(\n"
            + f"      header={self.header}\n"
            + f"      header_complete={self.header_complete}\n"
            + f"      header_type={self.header_type}\n"
            + f"      header_indent={self.header_indent}\n"
            + f"      indent_size={self.indent_size}\n"
            + ")"
        )


class Tokenizer:
    def __init__(
        self,
        file_name:str,
        text: str,  # Text to be tokenized
        indent_type=" ",  # which character to use for indentation,
        # if indent_type.lower() == "s" then we use spaces for indentation
        # if indent_type.lower() == "t" then we use tabs for indentation
        indent_size=4,  # How many indent characters in a single indent token
        supplied_spaces_explicitly=False,  # Did you supply --spaces explicitly?
    ):
        self.file = file_name
        self.text: str = text
        self.current_char: str = ""
        self.idx, self.ln, self.col = 0, 0, 0
        if len(text) != 0:
            self.current_char = self.text[0]
        self.tokens_list: list[Token] = []
        self.indent_stack = []  # how many indents currently
        self.indent_token_stack: List[Token] = []
        self.checked_indent = False
        self.lines: dict[int, Line] = {}
        self.last_line_break_index = -1

        self.indent_type: str = indent_type.lower()
        if self.indent_type not in (" ", "\t"):
            raise ValueError(f'{self.indent_type = } must be either " " or "\\t"')

        self.indent_size = indent_size

        # becomes True after this instance successfully executes tokenize()
        self.done = False

        self.supplied_spaces_explicitly = supplied_spaces_explicitly

        # Store left parentheses "( or [" tokens to enable multi-line statements
        self.left_parenthesis_stack: List[Token] = []

        self.blocks: List[Block] = []

        # True upon encountering keyword (end), False after finding its label
        self.end_string = False

        self.indent_name = "space" if self.indent_type == " " else "tab"

        self.indent_char = "+" if self.indent_name == "space" else "*"

        Block.lines_dict = self.lines

    def pos(self):
        return Pos(self.idx, self.col, self.ln)

    def current_line(self) -> Line:
        # VERY IMPORTANT NOTICE
        # When we encounter a \n during tokenization, we consider this \n as the end of some line
        # namely, the all characters preceding this \n up to the nearest \n but excluding it
        #
        # More clearly, when we encounter a line break (\n) called X
        # X is considered at the (END) of some line, after all this \n character is called (Line Break)
        # So we search backwards until we hit Y, which is file begin or another \n
        # so X's line is all characters between Y and X
        # and of course excluding both X and Y because we don't want \n in line representation

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

    def line_indented(self, line_index):
        line = self.lines[line_index].value
        line_caret = re.compile(r"[^\s]").search(string=line)
        if line_caret:
            line_caret = line_caret.start()
        else:
            line_caret = 0
        return self.indent_char * line_caret + line[line_caret:]

    def current_line_indented(self):
        return self.line_indented(self.ln)

    def advance(self, steps):
        self.idx = min(self.idx + steps, len(self.text))

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

        if (
            self.col == 0  # It's line head
            and not self.checked_indent  # We have not checked indentation in this line
            and len(self.left_parenthesis_stack) == 0  # this is a not a multi-line statement
        ):
            self.checked_indent = True
            current_line_object = self.current_line()
            current_line = current_line_object.value
            current_line_line_break = current_line_object.end
            first_non_white_space = re.compile(r"[^\s]").search(
                string=self.text, pos=self.idx, endpos=current_line_line_break
            )
            if first_non_white_space is None:
                # this line is empty or it is just whitespaces
                steps = len(current_line)
            else:
                captured_indent = self.text[self.idx : first_non_white_space.start()]

                # <======================================================================>
                # Indenting top level code error
                if (
                    not self.left_parenthesis_stack  # (Multi-line)ing is disable
                    # No active blocks, we are inside no block, we livin' in top level code
                    and not self.blocks
                    # So no active () or [] and no active blocks
                ) and captured_indent:  # Trying to add an actual indent
                    # Indentation Error: Indenting top-level code
                    error += f"Indentation Error in \"{self.file}\", line {self.ln + 1}:\n"
                    error += " " * 4 + "Indenting top-level code\n\n"
                    error += " " * 4
                    for c in captured_indent:
                        error += "+" if c == " " else "*"
                    error += current_line[len(captured_indent) :] + "\n"
                    error += " " * 4 + "^" * len(captured_indent) + "\n"
                    error += " " * 4 + "Found indentation, remove it\n"
                    # No need to see other errors
                    return error, None  # JUST IGNORE THIS TYPE-CHECKING ERROR
                # Indenting top level code error
                # <======================================================================>

                elif self.blocks and (  # Do checking when we have an active block
                    current_line[0] in (" ", "\t")
                    # Do not check indentation these separators
                    or first_non_white_space.group() not in ("#", ",", ";", ":", ")", "]", '"')
                ):
                    # <======================================================================>
                    # ERROR HANDLING
                    opposite_indent_name = "tab" if self.indent_name == "space" else "space"

                    # First check this captured_indent is matches self.indent_type
                    # To elaborate, check source code is not using tabs when spaces are enable, or vice versa
                    # And source code is not mixing tabs and spaces some where
                    opposite_type_detected = False
                    if (
                        "\t" in captured_indent and self.indent_name == "space"
                    ) or (  # Using tabs when indenting with spaces
                        " " in captured_indent and self.indent_name == "tab"
                    ):  # Using spaces when indenting with tabs
                        error += f"Indentation Error in \"{self.file}\", line {self.ln + 1}:\n"
                        error += " " * 4
                        error += f"Using (disabled) {opposite_indent_name}s with (enabled) {self.indent_name}s indentation\n\n"
                        error += " " * 4
                        for c in captured_indent:
                            error += "+" if c == " " else "*"
                        error += current_line[len(captured_indent) :] + "\n"
                        error += " " * 4
                        illegal_chars = 0
                        for c in captured_indent:
                            if c != self.indent_type:
                                error += "^"
                                illegal_chars += 1
                            else:
                                error += " "
                        error += "\n"
                        error += " " * 4 + f"Found {'one' if illegal_chars == 1 else illegal_chars} "
                        error += f"{opposite_indent_name}{'s' * int(illegal_chars != 1)}\n"
                        error += f"In every INDENT in this file, remove ALL {opposite_indent_name.upper()}S\n"
                        opposite_type_detected = True

                    if opposite_type_detected is False and (
                        (0 if not self.blocks[-1].header_indent else len(self.blocks[-1].header_indent.value)) < len(captured_indent)
                        and self.indent_size != 1
                        and (remaining := len(captured_indent) % self.indent_size) != 0
                    ):
                        if error != "":
                            error += "<======================================================================>\n"
                        UPPER = self.indent_size * (
                            len(captured_indent) // self.indent_size
                        )
                        error += f"Indentation Error \"{self.file}\", line {self.ln + 1}:\n"
                        error += " " * 4
                        error += f"Invalid indent of {remaining} {self.indent_name}{'' if remaining == 1 else 's'}\n\n"
                        error += " " * 4 + self.indent_char * len(captured_indent[UPPER:])
                        error += current_line[len(captured_indent) : ] + "\n"
                        error += " " * 4 + "^" * len(captured_indent[UPPER:]) + "\n"
                        if re.compile(r"[^\s]+").search(string=current_line).group() in ("end", "if", "else_if", "else"):
                            error += f"Remove {'this' if remaining == 1 else 'these'} {'one' if remaining == 1 else remaining} "
                        else:
                            error += f"Add another {'one' if (n:=self.indent_size-remaining) == 1 else n} "
                        error += f"{self.indent_name}{'' if remaining == 1 else 's'} "

                    if opposite_type_detected is False:
                        current_block = self.blocks[-1]

                        if current_block.header_indent:
                            current_block_header_indent = len(current_block.header_indent.value)
                        else:
                            current_block_header_indent = 0

                        next_thing = re.compile(r"[^\s]+").search(string=current_line).group()
                        if (
                            current_block.indent_size
                            and
                            len(captured_indent) <= current_block_header_indent
                            and
                            next_thing not in ("end", "else", "else_if")
                        ):
                            if error:
                                error += "<======================================================================>\n"

                            error += f"Indentation Error in \"{self.file}\", line {self.ln + 1}\n"
                            error += " " * 4
                            error += "Unexpected indentation\n\n"
                            error += " " + current_line + "\n" + " " * len(captured_indent) + "^" + "\n"
                            error += f"Indentation level in line {self.ln + 1} "
                            error += f"(level {len(captured_indent)//self.indent_size}) "
                            error += "does not match current block indentation level "
                            error += f"(level {current_block.indent_size//self.indent_size})"

                        elif (
                            not current_block.indent_size
                            and
                            len(captured_indent) <= current_block_header_indent
                        ):
                            if error:
                                error += "<======================================================================>\n"
                            error += f"Indentation Error in \"{self.file}\", line {self.ln + 1}\n"
                            error += " " * 4
                            error += "Expected indentation\n\n"
                            error += " " + current_line + "\n" + " " * len(captured_indent) + "^" + "\n"
                            error += f"Expected indentation level {current_block_header_indent // self.indent_size + 1} "
                            error += f"but found level {len(captured_indent) // self.indent_size}"

                    # ERROR HANDLING DONE
                    # <======================================================================>

                    if error == "":
                        # No errors
                        if len(self.indent_stack) == 0:
                            current_indent_level = 0
                        else:
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
                            self.indent_token_stack.append(token)
                        elif current_indent_level < len(captured_indent):
                            # INDENT
                            self.indent_stack.append(
                                len(captured_indent)
                            )  # Use captured_indent length to 0, 4, 8, 12, ... (indent_size 4)

                            self.blocks[-1].indent_size = len(
                                captured_indent
                            )  # JUST IGNORE THIS TYPE-CHECKING ERROR

                            token.name = "INDENT"
                            self.indent_token_stack.append(token)
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
            if self.blocks:
                if self.blocks[-1].header_type == Block.SINGLE:  # single line header
                    self.blocks[-1].header_complete = True
            self.end_string = False # because (end label) must be in single line
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

        elif self.current_char == '"':

            if string := STRING_PATTERN.match(string=self.text, pos=self.idx):
                # SUCCESSFULLY MATCHED A STRING
                match_value = string.group()
                token = Token(value=match_value)

                if self.end_string:
                    # this line is like: end "some text here"
                    token.name = "END_LABEL_STRING"
                    self.end_string = False
                else:
                    token.name = "STRING"

                token.begin = begin = self.pos()
                token.end = Pos(
                    begin.idx + len(token.value), begin.col + len(token.value), begin.ln
                )
                steps = len(token.value)

            else:
                # FOUND " with no matching "
                if error != "":
                    error += "<======================================================================>\n"
                error += f"Syntax Error in \"{self.file}\", line {self.ln + 1}\n"
                error += " " * 4 + "Unclosed \"\n\n"
                current_line = self.current_line().value
                error += " " * 4 + current_line + "\n"
                error += " " * 4 + " " * self.col + "^"

        elif name := NAME_PATTERN.match(string=self.text, pos=self.idx):
            # IDENTIFIER
            # an identifier or a keyword
            current_identifier = name.group()
            token = Token()
            token.begin = begin = self.pos()
            token.value = current_identifier
            token.end = Pos(
                idx=begin.idx + len(token.value),
                col=begin.col + len(token.value),
                ln=self.ln
            )

            if token.value in KEYWORDS:
                if token.value in ("not", "and", "or"):
                    token.name = "OPERATOR"
                else:
                    token.name = "KEYWORD"
                    if token.value == "end":
                        if (
                            self.left_parenthesis_stack
                            or (self.left_parenthesis_stack and self.end_string)
                        ): # multi-ling is not allowed with (end)
                            if error:
                                error += "<======================================================================>\n"
                            error += f"Error in \"{self.file}\", line {self.ln + 1}:\n"
                            error += " " * 4 + "Multi-lined end statement\n\n"
                            tok = self.left_parenthesis_stack[-1]
                            width = len(str(self.ln))
                            error += f"{tok.begin.ln:^{width}}:" + " " * 4 + self.lines[tok.begin.ln].value + "\n"
                            error += " " * 4 + " " * len(f"{tok.begin.ln:^{width}}:") + " " * tok.begin.col + "^" + "\n"
                            for ln_idx in range(tok.begin.ln+1, self.ln+1):
                                error += f"{ln_idx:^{width}}:" + " " * 4 + self.lines[ln_idx].value + "\n"
                            error += f"Remove ( above in line {tok.begin.ln}"
                        else:
                            self.end_string = True

                    elif token.value in BLOCK_STATEMENTS:
                        if self.left_parenthesis_stack:
                            # Multi-ling with block headers, something like this, NOT ALLOWED
                            # (if
                            #       x == 0)
                            #     pass
                            # end

                            # ALLOWED
                            # if (
                            #     x == 0
                            #     and y != 0
                            # )
                            #     pass
                            # end
                            if error != "":
                                error += "<======================================================================>\n"
                            error += f"Error in \"{self.file}\", line {self.ln + 1}:\n"
                            error += " " * 4 + "Multi-lining with block headers\n\n"
                            left_par_tok = self.left_parenthesis_stack[-1]
                            left_par_line = left_par_tok.begin.ln
                            width = max(
                                len(str(left_par_line)),
                                len(str(self.ln))
                            )

                            if self.indent_token_stack:
                                current_line_indent = len(self.indent_token_stack[-1].value)
                            else:
                                # no indentation in this line
                                current_line_indent = 0

                            error += f"{left_par_line:^{width}}:" + " " * 4
                            error += self.lines[left_par_line].value[current_line_indent:] + "\n"
                            error += len(f"{left_par_line:^{width}}:") * " " + " " * 4 + " " * left_par_tok.begin.col
                            error += "^" + "\n"
                            error += f"Remove this (, use it after '{token.value}'\n"
                        else:
                            self.blocks.append(
                                Block(
                                    header=[token],
                                    header_complete=(token.value == "else"),
                                    header_type=Block.SINGLE,
                                    header_indent=(
                                        None
                                        if not self.indent_token_stack
                                        else
                                        self.indent_token_stack[-1]
                                    ),
                                    indent_size=None
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
            if (
                (sep.group() == ")" or sep.group() == "]")
                and len(self.left_parenthesis_stack) == 0
            ):
                current_line_obj = self.current_line()
                current_line = current_line_obj.value
                first_non_white_space = (
                    re.compile(r"[^\s]").match(string=current_line).start()
                )
                error += f"Syntax Error in\"{self.file}\" line {self.ln + 1}:\n"
                error += " " * 4 + f"Unexpected {sep.group()}\n\n"
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
                    if self.end_string:
                        if error:
                            error += "<======================================================================>\n"
                        error += f"Error in \"{self.file}\", line {self.ln + 1}:\n"
                        error += " " * 4 + "Multi-lined end statement\n\n"
                        error += " " * 4 + self.current_line().value + "\n"
                        error += f"Remove ( and above"
                    else:
                        self.left_parenthesis_stack.append(token)
                        if self.blocks:
                            if not self.blocks[-1].header_complete:
                                self.blocks[-1].header_type = Block.MULTI
                elif token.value in (")", "]"):
                    # POP CURRENT MULTI-LINE STATEMENT STATE
                    if self.end_string:
                        if error:
                            error += "<======================================================================>\n"
                        error += f"Error in \"{self.file}\", line {self.ln + 1}:\n"
                        error += " " * 4 + "Multi-lined end statement\n\n"
                        tok = self.left_parenthesis_stack[-1]
                        for n in range(tok.begin.ln, self.ln+1):
                            error += " " * 4 + self.lines[n].value + "\n"
                        error += f"Remove ( and ) above"
                    else:
                        if self.blocks:
                            self.blocks[-1].add(token)
                            self.blocks[-1].header_complete = True
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
                tips += f"You used --{self.indent_name}s"

            tips += "\n"

            tips += (
                f"Indent type: {self.indent_name.title()}s\n"
                + f"Indent Size: {'One' if self.indent_size == 1 else self.indent_size} "
                + f"{self.indent_name.title()}{'' if self.indent_size == 1 else 's'}\n"
                + f"One Indent: {self.indent_char * self.indent_size}\n"
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

            if token is not None:
                self.tokens_list.append(token)
                if token.name in ("OUTDENT"):
                    self.indent_token_stack.append(token)

                if self.blocks:
                    self.blocks[-1].add(token)

            if error != "":
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
        file = path.abspath(args.file)
    else:
        source = args.source
        file = "<stdin>"

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
        file_name = file,
        text=source,
        indent_type=indent,
        indent_size=size,
        supplied_spaces_explicitly=supplied_spaces_explicitly,
    )
    for token in tokenizer:
        print(token)
