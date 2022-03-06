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

INT_PATTERN = re.compile(r"[+-]{0,1}\d+([eE][+-]{0,1}\d+){0,1}")

FLOAT_PATTERN = re.compile(
    r"[+-]{0,1}\d+[.]\d*([eE][+-]{0,1}\d+){0,1}|[+-]{0,1}\d*[.]\d+([eE][+-]{0,1}\d+){0,1}"
)

NUMBER_PATTERN = re.compile(FLOAT_PATTERN.pattern + "|" + INT_PATTERN.pattern)

STRING_PATTERN = re.compile(r'f{0,1}".*?(?<!\\)"')

INDENT_PATTERN = re.compile(r"[ ]{4}|[\t]")  # 4 consecutive spaces or a single tab

NAME_PATTERN = re.compile(r"[_a-zA-Z][_a-zA-Z0-9]*")

OPERATOR_PATTERN = re.compile(
    # ARITHMETIC_OPERATORS``
    r"\+{1,2}|"  # to match either + or ++
    r"-{1,2}|"  # to match either - or --
    r"\*|"
    r"/|"
    r"~"
    r"&"
    r"\|"  # r"|" will always match empty strings
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
    r"\+=|"
    r"-=|"
    r"\*=|"
    r"/=|"
    r"=~"
    r"=&"
    r"\|=|"  # r"|" will always match empty strin=gs
    r">>=|"
    r"<<=|"
)

SEPARATOR_PATTERN = re.compile(r";|:|,|\[|]|\(|\)|")
