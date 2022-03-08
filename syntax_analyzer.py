#!/usr/local/bin/python3.10

from tokenizer import *
from typing import Union, List
from dataclasses import dataclass


class Syntax_Tree_Node:
    def __init__(self):
        self.name: List[str] = []  # FORMAL_GRAMMAR entry hierarchy
        # something like: ["EXPRESSION", "SIMPLE_EXPRESSION", "NAME"]
        # Last element in self.name represents the FORMAL_GRAMMAR name of this object


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

# TYPE CLASS
class EXPRESSION_Node(Syntax_Tree_Node):
    # This FORMAL_GRAMMAR unit has these 2 kinds
    types = (
        "SIMPLE_EXPRESSION",
        "COMPOUND_EXPRESSION",
    )

    def __init__(self, type_name=""):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("EXPRESSION")


# TYPE CLASS
class EXPRESSION_SIMPLE_Node(EXPRESSION_Node):
    types = ("NAME", "LITERAL")

    def __init__(self, type_name=""):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("SIMPLE_EXPRESSION")


# TYPE CLASS
class EXPRESSION_COMPOUND_Node(EXPRESSION_Node):
    types = (
        "FUNCTION_CALL",
        "CONST_VAR_DEFINITION",
        "ARRAY_SUBSCRIPTION",
        "OPERATOR_EXPRESSION",
    )

    def __init__(self, type_name=""):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("COMPOUND_EXPRESSION")


# <====================================================================================================>
# FORMAL_GRAMMAR units with no types have no class attribute (type), instead they have class attribute (parts)
# AND also they have special instance attributes which vary between different classes
# For instance, object attributes of ARRAY_SUBSCRIPTION will not be the same as EXPRESSIONS_LIST
# <====================================================================================================>


# CONCRETE CLASS
class EXPRESSION_ARRAY_SUBSCRIPTION_Node(EXPRESSION_SIMPLE_Node):
    parts = ("NAME", "[", "NON_NEGATIVE_INTEGER", "]")

    def __init__(self, array_name="", non_negative_integer=0):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("ARRAY_SUBSCRIPTION")

        if non_negative_integer < 0:
            raise ValueError(f"{non_negative_integer} is less than 0")
        else:
            self.array_name = array_name
            self.non_negative_integer = non_negative_integer


# CONCRETE CLASS
class EXPRESSION_NAME_Node(EXPRESSION_SIMPLE_Node):
    parts = ("NAME",)  # Since it's a single unit in and of itself

    def __init__(self, name_string=""):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("NAME")
        self.name_string = name_string  # Class-Object-specifics attributes


# TYPE CLASS
class EXPRESSION_LITERAL_Node(EXPRESSION_SIMPLE_Node):
    types = ("NUMBER", "STRING")

    def __init__(self, type_name=""):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("LITERAL")

        # this (type_name) must be EXPRESSION_Node.types
        # This EXPRESSION_LITERAL_Node object must have a type
        # and this type must be in EXPRESSION_LITERAL_Node.types tuple defined above
        self.type_name = type_name


# CONCRETE CLASS
class EXPRESSION_NUMBER_Node(EXPRESSION_SIMPLE_Node):
    parts = ("NUMBER",)  # Since it's a single unit in and of itself

    def __init__(self, number_value=""):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("NUMBER")
        if not NUMBER_PATTERN.fullmatch(number_value):
            raise ValueError(f"{number_value} is not a valid numeric literal")
        self.number_value = number_value  # Class-Object-specifics attributes


# CONCRETE CLASS
class EXPRESSION_STRING_Node(EXPRESSION_SIMPLE_Node):
    parts = ("STRING",)  # Since it's a single unit in and of itself

    def __init__(self, string_value=""):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("STRING")
        self.string_value = string_value  # Class-Object-specifics attributes


# CONCRETE CLASS
class EXPRESSION_EXPRESSIONS_LIST_Node(EXPRESSION_SIMPLE_Node):
    parts = ("EXPRESSIONS",)

    def __init__(self, expressions_list: List[EXPRESSION_Node] = None):
        super().__init__()
        if expressions_list is None:
            expressions_list: List[EXPRESSION_Node] = []

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("EXPRESSIONS_LIST")
        self.expressions_list: List[
            EXPRESSION_Node
        ] = expressions_list  # Class-Object-specifics attributes


# CONCRETE CLASS
class EXPRESSION_FUNCTION_CALL_Node(EXPRESSION_SIMPLE_Node):
    parts = ("NAME", "EXPRESSIONS_LIST")

    def __init__(
        self, function_name="", expressions_list: List[EXPRESSION_Node] = None
    ):
        super().__init__()
        if expressions_list is None:
            expressions_list: List[EXPRESSION_Node] = []

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("FUNCTION_CALL")
        self.expressions_list: List[
            EXPRESSION_Node
        ] = expressions_list  # Class-Object-specifics attributes
        self.function_name = function_name


class Result:
    def __init__(self, error: str = "", astNode: Syntax_Tree_Node = Syntax_Tree_Node()):
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
        refs = (
            {}
        )  # In case we find multiple definitions, this dict records which variables/constants are references
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
