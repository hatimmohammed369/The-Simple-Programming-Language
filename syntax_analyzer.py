#!/usr/local/bin/python3.10

from asyncio import current_task
from tokenizer import *
from typing import Union, List
from dataclasses import dataclass


@dataclass(init=True, repr=True)
class AstNode:
    name: str = ""


class CONST_VAR_DEFINITION_AstNode(AstNode):
    def __init__(self):
        self.name = "CONST_VAR_DEFINITION"


class Result:
    def __init__(self, error: str = "", astNode: AstNode = AstNode()):
        self.error = error
        self.ast_node = astNode


class SyntaxAnalyzer:
    def __init__(self, tokenizer_object: Tokenizer):
        self.tok_obj = tokenizer_object
        if self.tok_obj.done is False:
            self.tok_obj.tokenize()

        # Which position in self.tok_obj.tokenst_list
        self.idx = 0

        # self.tok_obj.tokens_list[self.idx], current token
        self.cur_tok: Union[Token, None] = self.tok_obj.tokens_list[self.idx]

        # becomes True after analyze() successfully execute
        self.done = False

    def __len__(self):
        return len(self.tok_obj.tokens_list)

    def __getitem__(self, key):
        return self.tok_obj.tokens_list[key]

    def advance(self):
        self.idx += 1
        if self.idx < len(self):
            self.cur_tok: Union[Token, None] = self[self.idx]
        else:
            self.cur_tok: Union[Token, None] = None
        return self

    def EXPRESSION(self) -> Result:
        res = Result()
        return res

    def CONST_VAR_DEFINITION(self) -> Result:
        successful_definitions = 0
        res = Result()
        phase = "NAME"
        is_ref = False
        refs = {}
        while self.cur_tok is not None:
            if phase == "NAME":
                # Looking for NAME
                if (
                    NAME_PATTERN.fullmatch(self.cur_tok.value)
                    and self.cur_tok.value not in KEYWORDS
                ):
                    # NAME VALID
                    phase = ":"
                else:
                    # NAME INVALID
                    ln = self.cur_tok.begin.ln
                    res = Result(
                        error=f"Syntax Error in line {ln + 1}:\n"
                        + "    "
                        + self.tok_obj.lines[ln].value
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + "^" * len(self.cur_tok.value)
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + f"Expected a valid variable/constant name, but found '{self.cur_tok.value}'",
                        astNode=None,
                    )
                    break
            elif phase == ":":
                # Looking for :
                if self.cur_tok.value == ":":
                    # FOUND :
                    phase = "const-var"
                else:
                    # FOUND NO :
                    ln = self.cur_tok.begin.ln
                    res = Result(
                        error=f"Syntax Error in line {ln + 1}:\n"
                        + "    "
                        + self.tok_obj.lines[ln].value
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + "^" * len(self.cur_tok.value)
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + f"Expected a single colon (:), but found '{self.cur_tok.value}'",
                        astNode=None,
                    )
                    break
            elif phase == "const-var":
                # Looking for either const or var, not both
                if self.cur_tok.value in ("const", "var"):
                    # FOUND const/var
                    phase = "TYPE_NAME"
                else:
                    # FOUND NO const/var
                    ln = self.cur_tok.begin.ln
                    res = Result(
                        error=f"Syntax Error in line {ln + 1}:\n"
                        + "    "
                        + self.tok_obj.lines[ln].value
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + "^" * len(self.cur_tok.value)
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + f"Expected either lowercase (const) or lowercase (var), "
                        + "but found neither, actually found '{self.cur_tok.value}'",
                        astNode=None,
                    )
                    break
            elif phase == "TYPE_NAME":
                # Looking for a typename
                if self.cur_tok.value in PRIMITIVE_DATA_TYPES:
                    # FOUND A VALID TYPE_NAME
                    phase = "&"
                else:
                    # FOUND NO VALID TYPE_NAME
                    ln = self.cur_tok.begin.ln
                    res = Result(
                        error=f"Syntax Error in line {ln + 1}:\n"
                        + "    "
                        + self.tok_obj.lines[ln].value
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + "^" * len(self.cur_tok.value)
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + f"No type with name '{self.cur_tok.value}'",
                        astNode=None,
                    )
                    break
            elif phase == "&":
                # Looking for the (optional) reference & operator
                if self.cur_tok.value == "&":
                    # FOUND &
                    is_ref = True
                    phase = ":="
                elif self.cur_tok.value == ":=":
                    is_ref = False
                    phase = "EXPRESSION"
                else:
                    # FOUND NEITHER & or :=
                    ln = self.cur_tok.begin.ln
                    res = Result(
                        error=f"Syntax Error in line {ln + 1}:\n"
                        + "    "
                        + self.tok_obj.lines[ln].value
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + "^" * len(self.cur_tok.value)
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + f"Expected either & (for references) or := (for definition assignment), "
                        + "but found neither, actually found '{self.cur_tok.value}'",
                        astNode=None,
                    )
                    break
            elif phase == ":=":
                # Looking for :=
                if self.cur_tok.value == ":=":
                    # FOUND :=
                    phase = "EXPRESSION"
                else:
                    # FOUND NO :=
                    ln = self.cur_tok.begin.ln
                    res = Result(
                        error=f"Syntax Error in line {ln + 1}:\n"
                        + "    "
                        + self.tok_obj.lines[ln].value
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + "^" * len(self.cur_tok.value)
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + f"Expected :=, but found '{self.cur_tok.value}'",
                        astNode=None,
                    )
                    break
            elif phase == "EXPRESSION":
                pass

            if not res.error:
                self.advance()
        return res

    def analyze(self):
        while self.cur_tok:
            if self.cur_tok.value == "define":
                # CONST_VAR_DEFINITION
                self.advance()
                res = self.CONST_VAR_DEFINITION()
                if res.error:
                    print(res.error)
                    exit(0)
        self.done = True
        return self


# End Of Class SyntaxAnalyzer
