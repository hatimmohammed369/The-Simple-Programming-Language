# KEYWORDS / OPERATORS / ...
# You know, those sorts of things
import re

KEYWORDS = (
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
    "while",
    "break",
    "continue",
    "pass",
)

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
    # ARITHMETIC_OPERATORS``
    r"[+]{1,2}|"  # to match either + or ++
    r"-{1,2}|"  # to match either - or --
    r"[*]|"
    r"/|"
    r"~|"
    r"&|"
    r"[|]|"  # r"|" will always match empty strings
    r">>|"
    r"<<|"
    # LOGICAL_OPERATORS
    r"==|"
    r"!=|"
    r"<|"
    r"<=|"
    r">|"
    r">=|"
    r"not|"
    r"and|"
    r"or|"
    # ASSIGNMENT_OPERATORS
    r"=|"
    r":=|"
    r"[+]=|"
    r"-=|"
    r"[*]=|"
    r"/=|"
    r"~=|"
    r"&=|"
    r"[|]=|"
    r">>=|"
    r"<<="
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
