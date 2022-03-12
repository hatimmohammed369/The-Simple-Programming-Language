from dataclasses import dataclass
from typing import Any

# KEYWORDS / OPERATORS / ...
# You know, those sorts of things
import re

KEYWORDS = (
    "define",
    "var",
    "const",
    "int",
    "real",
    "string",
    "bool",
    "not",
    "and",
    "or",
    "true",
    "false",
    "array",
    "ref_of",
    "fn",
    "return",
    "if",
    "else",
    "else_if",
    "for",
    "in",
    "while",
    "break",
    "continue",
    "pass",
)

PRIMITIVE_DATA_TYPES = ("int", "real", "bool", "string", "array")

OPERATORS = (
    # ARITHMETIC_OPERATORS
    "+",
    "-",
    "*",
    "/",
    "~",
    "&",
    "|",
    "^",
    ">>",
    "<<",
    # LOGICAL_OPERATORS
    "==",
    "!=",
    "<",
    "<=",
    ">",
    ">=",
    "not",
    "and",
    "or",
    # ASSIGNMENT_OPERATORS
    ":=",
    "=",
    "+=",
    "-=",
    "*=",
    "/=",
    "~=",
    "&=",
    "|=",
    "^=",
    ">>=",
    "<<=",
)

SEPARATORS = ("[", "]", "(", ")", ",", ":", ";")

INT_PATTERN = re.compile(
    r"[+-]{0,1}[0-9]+([eE][+-]{0,1}[0-9]+){0,1}(?![.]([0-9]*[eE][+-]{0,1}[0-9]+|[0-9]+([eE][-+]{0,1}[0-9]+){0,1}))"
)  # Match integer ONLY IF it's NOT before a fractional part (e.g, .2384)
# This ensure INT_PATTERN matches ONLY integers

FLOAT_PATTERN = re.compile(
    r"[+-]{0,1}[0-9]+[.][0-9]*([eE][+-]{0,1}[0-9]+){0,1}|[+-]{0,1}[0-9]*[.][0-9]+([eE][+-]{0,1}[0-9]+){0,1}"
)

NUMBER_PATTERN = re.compile(FLOAT_PATTERN.pattern + "|" + INT_PATTERN.pattern)

STRING_PATTERN = re.compile(
    r'".*?(?<!\\)"'
)  # Match (matching ") ONLY IF this (matching ") is not preceded by \
# This way we can strings like "This is "A String" inside another"

INDENT_PATTERN = re.compile(r"[ ]{4}|[\t]")  # 4 consecutive spaces or a single tab

NAME_PATTERN = re.compile(r"[_a-zA-Z][_a-zA-Z0-9]*")

OPERATOR_PATTERN = re.compile(
    r"not|"
    r"and|"
    r"or|"
    r"[+][+]|"
    r"[+]=|"
    r"--|"
    r"-=|"
    r"[*]=|"
    r"/=|"
    r"~=|"
    r"&=|"
    r"[|]=|"
    r"\^="
    r">>=|"
    r">>|"
    r"<<=|"
    r"<<=|"
    r":=|"
    r"==|"
    r"!=|"
    r"<=|"
    r">=|"
    r"[+]|"
    r"-|"
    r"[*]|"
    r"/|"
    r"~|"
    r"&|"
    r"[|]|"
    r"\^|"
    r"<|"
    r">|"
    r"="
)

SEPARATOR_PATTERN = re.compile(
    r";"
    + "|"
    + r":"
    + "|"
    + r","
    + "|"
    + r"\["
    + "|"
    + r"]"
    + "|"
    + r"\("
    + "|"
    + r"\)"
)

ARRAY_TYPE_PATTERN = re.compile(
    rf"array\[{INT_PATTERN.pattern}:{NAME_PATTERN.pattern}]"
)


@dataclass(init=True, repr=True)
class Result:
    """
    A general wrapper class used as return for operation which may fail
    """

    error_msg: str = ""  # Error message on failure
    result = object()  # resulting object
    # Instead of returning (result) only on success,
    # having it on failure is also valuable since we can diagnose the source of error use the invalid (result)
