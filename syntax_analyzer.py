from tokenizer import *
from typing import List

# BASE CLASS
class Syntax_Tree_Node:
    def __init__(self):
        self.name: List[str] = []  # FORMAL_GRAMMAR entry hierarchy
        # something like: ["EXPRESSION", "SIMPLE_EXPRESSION", "NAME"]
        # Last element in self.name represents the FORMAL_GRAMMAR name of this object


# end class Syntax_Tree_Node

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

    def __init__(self):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("EXPRESSION")


# TYPE CLASS
class EXPRESSION_SIMPLE_Node(EXPRESSION_Node):
    types = ("NAME", "LITERAL")

    def __init__(self):
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

    def __init__(self):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("COMPOUND_EXPRESSION")


# <====================================================================================================>
# FORMAL_GRAMMAR units with no types have no class attribute (type), instead they have class attribute (parts)
# AND also they have special instance attributes which vary between different classes
# For instance, object attributes of ARRAY_SUBSCRIPTION will not be the same as EXPRESSIONS_LIST
#
# All data validation is done in code creating _Node objects
# <====================================================================================================>


# CONCRETE CLASS
class EXPRESSION_NAME_Node(EXPRESSION_SIMPLE_Node):
    parts = ("NAME",)  # Since it's a single unit in and of itself

    def __init__(self, name_string: Token = Token(), is_ref: bool = False):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("NAME")
        self.name_string: Token = name_string  # Class-Object-specifics attributes
        self.is_ref: bool = is_ref  # this name is reference


# CONCRETE CLASS
class EXPRESSION_NUMBER_Node(EXPRESSION_SIMPLE_Node):
    parts = ("NUMBER",)  # Since it's a single unit in and of itself

    def __init__(self, number_value: Token = Token()):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("NUMBER")
        self.number_value: Token = number_value  # Class-Object-specifics attributes


# CONCRETE CLASS
class EXPRESSION_ARRAY_SUBSCRIPTION_Node(EXPRESSION_SIMPLE_Node):
    parts = ("NAME", "[", "NON_NEGATIVE_INTEGER", "]")

    def __init__(
        self,
        array_name: EXPRESSION_NAME_Node = EXPRESSION_NAME_Node(),
        left_square_bracket: Token = Token(),
        index: Token = Token(),
        right_square_bracket: Token = Token(),
    ):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("ARRAY_SUBSCRIPTION")

        self.array_name: EXPRESSION_NAME_Node = array_name
        self.left_square_bracket: Token = left_square_bracket
        self.index: Token = index
        self.right_square_bracket: Token = right_square_bracket


# TYPE CLASS
class EXPRESSION_LITERAL_Node(EXPRESSION_SIMPLE_Node):
    types = ("NUMBER", "STRING")

    def __init__(self):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("LITERAL")


# CONCRETE CLASS
class EXPRESSION_STRING_Node(EXPRESSION_SIMPLE_Node):
    parts = ("STRING",)  # Since it's a single unit in and of itself

    def __init__(self, string_value: Token = Token()):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("STRING")
        self.string_value: Token = string_value  # Class-Object-specifics attributes


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
        self,
        function_name: EXPRESSION_NAME_Node = EXPRESSION_NAME_Node(),
        expressions_list: EXPRESSION_EXPRESSIONS_LIST_Node = EXPRESSION_EXPRESSIONS_LIST_Node(),
    ):
        super().__init__()

        # Last element in this list tells us exactly which FORMAL_GRAMMAR unit this object is
        self.name.append("FUNCTION_CALL")
        self.expressions_list: EXPRESSION_EXPRESSIONS_LIST_Node = (
            expressions_list  # Class-Object-specifics attributes
        )
        self.function_name: EXPRESSION_NAME_Node = function_name


# CONCRETE CLASS
class TYPE_Node(Syntax_Tree_Node):
    parts = ("const_var", "type_name", "ref_op")

    def __init__(
        self,
        const_var: Token = Token(),
        type_name: Token = Token(),
        ref_op: Token = Token(),
    ):
        super().__init__()
        self.name.append("TYPE")
        self.const_var: Token = const_var
        self.type_name: Token = type_name
        self.ref_op: Token = ref_op


# CONCRETE CLASS
class EXPRESSION_CONST_VAR_DEFINITION_BODY_Node(Syntax_Tree_Node):
    parts = ("NAME", "COLON", "TYPE", ":=", "EXPRESSION")

    def __init__(
        self,
        name_string: EXPRESSION_NAME_Node = EXPRESSION_NAME_Node(),
        colon=Token(),
        type_name=TYPE_Node(),
        colon_equal: Token = Token(),
        expression=EXPRESSION_Node(),
    ):
        super().__init__()
        self.name_string: EXPRESSION_NAME_Node = name_string
        self.colon: Token = colon
        self.type_name: TYPE_Node = type_name
        self.colon_equal: Token = colon_equal
        self.expression: EXPRESSION_Node = expression


# CONCRETE CLASS
class EXPRESSION_CONST_VAR_DEFINITION_Node(EXPRESSION_COMPOUND_Node):
    parts = ("define", "NAME", ":", "TYPE", ":=", "EXPRESSION")

    def __init__(
        self,
        define=Token(),
        name_colon_type_list: List[EXPRESSION_CONST_VAR_DEFINITION_BODY_Node] = None,
    ):
        if name_colon_type_list is None:
            name_colon_type_list: List[EXPRESSION_CONST_VAR_DEFINITION_BODY_Node] = []

        self.define: Token = (
            define  # A helpful variable to track where this CONST_VAR_DEFINITION
        )

        # This variable contains all (NAME : TYPE) chucks of this CONST_VAR_DEFINITION
        self.name_colon_type_list: List[
            EXPRESSION_CONST_VAR_DEFINITION_BODY_Node
        ] = name_colon_type_list


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
        self.cur_tok: Token = self.tok_obj.tokens_list[self.idx]

        # becomes True after analyze() successfully execute
        self.done = False

    def __len__(self):
        return len(self.tok_obj.tokens_list)

    def __getitem__(self, key):
        return self.tok_obj.tokens_list[key]

    def advance(self):
        if self.idx <= len(self):
            self.idx += 1

        if self.idx < len(self):
            self.cur_tok: Token = self[self.idx]
        else:
            self.cur_tok: Token = None
        return self

    def EXPRESSION(self) -> List[Result]:
        res = [Result()]
        return res

    def CONST_VAR_DEFINITION(self) -> List[Result]:
        # When calling this method, self.cur_tok.value must be "define"
        res = [Result()]
        tree_node = EXPRESSION_CONST_VAR_DEFINITION_Node(
            define=self.cur_tok
        )  # This node holds the current (CONST_VAR_DEFINITION) if any
        self.advance()
        phase = "NAME"
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
                    tree_node.name_colon_type_list.append(  # Constructing this CONST_VAR_DEFINITION
                        EXPRESSION_CONST_VAR_DEFINITION_BODY_Node(  # Create a new (NAME : TYPE := EXPRESSION) object
                            name_string=EXPRESSION_NAME_Node(  # Setting the name part with this name we just found, namely self.cur_tok.value
                                name_string=self.cur_tok,  # the actual name, which is Token
                            )
                        )
                    )
                else:
                    # NAME INVALID
                    ln = self.cur_tok.begin.ln
                    res[0] = Result(
                        error=f"Syntax Error in line {ln + 1}:\n"
                        + "    "
                        + self.tok_obj.lines[ln].value
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + "^" * len(self.cur_tok.value)
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + f"Expected a valid variable/constant name, "
                        + "but found '{self.cur_tok.value}'",
                        astNode=None,
                    )
                    break

            elif phase == ":":
                # Looking for :
                if self.cur_tok.value == ":":
                    # FOUND :
                    phase = "const-var"
                    tree_node.name_colon_type_list[
                        -1
                    ].colon = self.cur_tok  # the : in (NAME : TYPE := EXPRESSION)
                else:
                    # FOUND NO :
                    ln = self.cur_tok.begin.ln
                    res[0] = Result(
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
                    tree_node.name_colon_type_list[-1].type_name = TYPE_Node(
                        const_var=self.cur_tok  # the const/var in (NAME : const int := EXPRESSION) for instance
                    )
                else:
                    # FOUND NO const/var
                    ln = self.cur_tok.begin.ln
                    res[0] = Result(
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
                    tree_node.name_colon_type_list[
                        -1
                    ].type_name.type_name = (
                        self.cur_tok
                    )  # the type name in (x: const int := -2834745) for instance
                else:
                    # FOUND NO VALID TYPE_NAME
                    ln = self.cur_tok.begin.ln
                    res[0] = Result(
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
                    # This name is a reference
                    phase = ":="
                    tree_node.name_colon_type_list[
                        -1
                    ].name_string.is_ref = True  # This name is indeed a reference
                elif self.cur_tok.value == ":=":
                    phase = "EXPRESSION"
                    tree_node.name_colon_type_list[
                        -1
                    ].name_string.is_ref = False  # Just for clarification
                else:
                    # FOUND NEITHER & or :=
                    ln = self.cur_tok.begin.ln
                    res[0] = Result(
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
                    tree_node.name_colon_type_list[
                        -1
                    ].colon_equal = (
                        self.cur_tok
                    )  # The := in (NAME : TYPE := EXPRESSION)
                else:
                    # FOUND NO :=
                    ln = self.cur_tok.begin.ln
                    res[0] = Result(
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
                # Looking for an expression
                # expr_res = self.EXPRESSION()
                if NUMBER_PATTERN.fullmatch(
                    self.cur_tok.value
                ):  # For simplicity use numbers, for now
                    # FOUND A VALID EXPRESSION
                    phase = ",-;"
                    tree_node.name_colon_type_list[
                        -1
                    ].expression = EXPRESSION_NUMBER_Node(number_value=self.cur_tok)
                else:
                    # FOUND NO VALID EXPRESSION
                    ln = self.cur_tok.begin.ln
                    res[0] = Result(
                        error=f"Syntax Error in line {ln + 1}:\n"
                        + "    "
                        + self.tok_obj.lines[ln].value
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + "^" * len(self.cur_tok.value)
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + f"Expected an expression (variable, constant, number, string, array expression), "
                        + "but found '{self.cur_tok.value}'",
                        astNode=None,
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
                    phase = "NAME"
                else:
                    # FOUND NEITHER (,) nor (;)
                    ln = self.cur_tok.begin.ln
                    res[0] = Result(
                        error=f"Syntax Error in line {ln + 1}:\n"
                        + "    "
                        + self.tok_obj.lines[ln].value
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + "^" * len(self.cur_tok.value)
                        + "\n"
                        + " " * (self.cur_tok.end.col + (4 - len(self.cur_tok.value)))
                        + f"Expected either , (comma) or ; (semi-colon), but found neither, actually found '{self.cur_tok.value}'",
                        astNode=None,
                    )
                    break

            if old_phase != phase:
                self.advance()
        return res

    def analyze(self):
        while self.cur_tok is not None:
            if self.cur_tok.value == "define":
                # CONST_VAR_DEFINITION
                res = self.CONST_VAR_DEFINITION()
                if res[-1].error:
                    print(res[-1].error)
                    exit(0)
            self.advance()  # added this because code was stuck in a loop
            # Even thought things are OK
            # we need self.cur_tok as None to break out of this while
        self.done = True
        return self


# End Of Class SyntaxAnalyzer
