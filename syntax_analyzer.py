#!/usr/local/bin/python3.10

from asyncio import current_task
from tokenizer import *
from typing import Union, List
from dataclasses import dataclass


class AST_Node:
    def __init__(self):
        self.name: List[str] = []


# EXPRESSION: SIMPLE_EXPRESSION | COMPOUND_EXPRESSION
#
# SIMPLE_EXPRESSION: NAME | LITERAL
#
# COMPOUND_EXPRESSION: FUNCTION_CALL | CONST_VAR_DEFINITION | ARRAY_SUBSCRIPTION | OPERATOR_EXPRESSION
#
# ARRAY_SUBSCRIPTION: NAME '[' NON_NEGATIVE_INTEGER ']'
#
# LITERAL: NUMBER | STRING
#
# FUNCTION_CALL: NAME '(' EXPRESSIONS_LIST ')'
#
# EXPRESSIONS_LIST: EXPRESSION ( ',' EXPRESSION )*
#
# OPERATOR_EXPRESSION: UNARY_OPERATOR SIMPLE_EXPRESSION | SIMPLE_EXPRESSION ( BINARY_OPERATOR SIMPLE_EXPRESSION )+
class EXPRESSION_AST_Node(AST_Node):
    types = ["SIMPLE_EXPRESSION", "COMPOUND_EXPRESSION"]

    def __init__(self, type_name: str = ""):
        self.name.append("EXPRESSION")
        self.type_name: List[str] = [type_name]


class SIMPLE_EXPRESSION_AST_Node(EXPRESSION_AST_Node):
    types = ["NAME", "LITERAL"]

    def __init__(self, type_name=""):
        self.name.append("SIMPLE_EXPRESSION")
        self.type_name.append(type_name)


class COMPOUND_EXPRESSION_AST_Node(EXPRESSION_AST_Node):
    types = [
        "FUNCTION_CALL",
        "CONST_VAR_DEFINITION",
        "ARRAY_SUBSCRIPTION",
        "OPERATOR_EXPRESSION",
    ]

    def __init__(self, type_name=""):
        self.name.append("COMPOUND_EXPRESSION")
        self.type_name.append(type_name)


class COMPOUND_EXPRESSION_ARRAY_SUBSCRIPTION_AST_Node(COMPOUND_EXPRESSION_AST_Node):
    parts = ["NAME", "[", "NON_NEGATIVE_INTEGER", "]"]

    def __init__(self, array_name="", non_negative_number: int = 0):
        if non_negative_number < 0:
            raise ValueError("{non_negative_number} is less than zero")
        else:
            self.array_name = array_name
            self.non_negative_number: int = non_negative_number


class SIMPLE_EXPRESSION_LITERAL_AST_Node(SIMPLE_EXPRESSION_AST_Node):
    types = ["NAME", "STRING"]

    def __init__(self, literal_value=""):
        self.type_name.append("LITERAL")
        self.literal_value = literal_value


class EXPRESSIONS_LIST_AST_Node(AST_Node):
    def __init__(self, expressions_list: List[EXPRESSION_AST_Node] = None):
        if expressions_list is None:
            expressions_list: List[EXPRESSION_AST_Node] = []
        self.expressions_list: List[EXPRESSION_AST_Node] = expressions_list
        pass


class COMPOUND_EXPRESSION_FUNCTION_CALL_AST_Node(COMPOUND_EXPRESSION_AST_Node):
    parts = ["NAME", "(", "EXPRESSIONS_LIST", ")"]

    def __init__(
        self, function_name="", expressions_list: List[EXPRESSION_AST_Node] = None
    ):
        if expressions_list is None:
            expressions_list: List[EXPRESSION_AST_Node] = []
        self.type_name.append("FUNCTION_CALL")
        self.function_name = function_name
        self.expressions_list: List[EXPRESSION_AST_Node] = expressions_list


class COMPOUND_EXPRESSION_OPERATOR_EXPRESSION_AST_Node(COMPOUND_EXPRESSION_AST_Node):
    types = ["UNARY_OPERATOR", "BINARY_OPERATOR"]

    def __init__(self):
        self.type_name.append("OPERATOR_EXPRESSION")


# CONST_VAR_DEFINITION: 'define' (NAME ':' TYPE ':=' EXPRESSION)+
# TODO: Add an attribute to indicate whether this CONST_VAR_DEFINITION is a (name) or (reference)
class CONST_VAR_DEFINITION_AST_NODE(EXPRESSION_AST_Node):
    @dataclass(init=True, repr=True)
    class CONST_VAR_DEFINITION_BODY:
        """
        Represents the (NAME ':' TYPE ':=' EXPRESSION) part
        """

        NAME: str = ""
        # TYPE: TYPE_AST_NODE = TYPE_AST_NODE()

    pass


class Result:
    def __init__(self, error: str = "", astNode: AST_Node = AST_Node()):
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

    # EXPRESSION: NAME | LITERAL | FUNCTION_CALL | CONST_VAR_DEFINITION | ARRAY_SUBSCRIPTION
    def EXPRESSION(self) -> List[Result]:
        res = [Result()]
        return res

    def CONST_VAR_DEFINITION(self) -> List[Result]:
        successful_definitions = 0
        res = [Result()]
        phase = "NAME"
        is_ref = False  # If current definition is making a reference
        refs = {}
        while self.cur_tok is not None:
            old_phase = phase
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
                    res.append(
                        Result(
                            error=f"Syntax Error in line {ln + 1}:\n"
                            + "    "
                            + self.tok_obj.lines[ln].value
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + "^" * len(self.cur_tok.value)
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + f"Expected a valid variable/constant name, but found '{self.cur_tok.value}'",
                            astNode=None,
                        )
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
                    res.append(
                        Result(
                            error=f"Syntax Error in line {ln + 1}:\n"
                            + "    "
                            + self.tok_obj.lines[ln].value
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + "^" * len(self.cur_tok.value)
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + f"Expected a single colon (:), but found '{self.cur_tok.value}'",
                            astNode=None,
                        )
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
                    res.append(
                        Result(
                            error=f"Syntax Error in line {ln + 1}:\n"
                            + "    "
                            + self.tok_obj.lines[ln].value
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + "^" * len(self.cur_tok.value)
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + f"Expected either lowercase (const) or lowercase (var), "
                            + "but found neither, actually found '{self.cur_tok.value}'",
                            astNode=None,
                        )
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
                    res.append(
                        Result(
                            error=f"Syntax Error in line {ln + 1}:\n"
                            + "    "
                            + self.tok_obj.lines[ln].value
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + "^" * len(self.cur_tok.value)
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + f"No type with name '{self.cur_tok.value}'",
                            astNode=None,
                        )
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
                    res.append(
                        Result(
                            error=f"Syntax Error in line {ln + 1}:\n"
                            + "    "
                            + self.tok_obj.lines[ln].value
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + "^" * len(self.cur_tok.value)
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + f"Expected either & (for references) or := (for definition assignment), "
                            + "but found neither, actually found '{self.cur_tok.value}'",
                            astNode=None,
                        )
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
                    res.append(
                        Result(
                            error=f"Syntax Error in line {ln + 1}:\n"
                            + "    "
                            + self.tok_obj.lines[ln].value
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + "^" * len(self.cur_tok.value)
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + f"Expected :=, but found '{self.cur_tok.value}'",
                            astNode=None,
                        )
                    )
                    break

            elif phase == "EXPRESSION":
                # Looking for an expression
                expr_res = self.EXPRESSION()
                if not expr_res.error:
                    # FOUND A VALID EXPRESSION
                    phase = ",-;"
                else:
                    # FOUND NO VALID EXPRESSION
                    ln = self.cur_tok.begin.ln
                    res.append(
                        Result(
                            error=f"Syntax Error in line {ln + 1}:\n"
                            + "    "
                            + self.tok_obj.lines[ln].value
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + "^" * len(self.cur_tok.value)
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + f"Expected an expression (variable, constant, number, string, array expression), but found '{self.cur_tok.value}'",
                            astNode=None,
                        )
                    )
                    break

            elif phase == ",-;":
                # Expecting either , or ;, but not both
                if self.cur_tok.value == ";":
                    # End Of Statement
                    return res
                elif self.cur_tok.value == ",":
                    # Successful definition was done
                    # There is another definition coming on the way!
                    successful_definitions += 1
                    phase = "NAME"
                else:
                    # FOUND NEITHER (,) nor (;)
                    ln = self.cur_tok.begin.ln
                    res.append(
                        Result(
                            error=f"Syntax Error in line {ln + 1}:\n"
                            + "    "
                            + self.tok_obj.lines[ln].value
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + "^" * len(self.cur_tok.value)
                            + "\n"
                            + " "
                            * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                            + f"Expected either , (comma) or ; (semi-colon), but found neither, actually found '{self.cur_tok.value}'",
                            astNode=None,
                        )
                    )
                    break

            if old_phase != phase:
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
