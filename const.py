import re

DATA_TYPES = ("int", "float", "string", "boolean", "array", "null")

KEYWORDS = (
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
    "in",
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
    "loop",
    "foreach",
    "match",
    "case",
    "default",
    "end",
    "function",
    "return",
    "returns",
)

BLOCK_STATEMENTS = ("if", "foreach", "while", "loop", "match", "function")

SEPARATORS = (
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
    "+=",
    "~",
    "&",
    "|",
    "<<",
    ">>",
    "<",
    "<=",
    ">",
    ">=",
    "==",
    "!=",
    "->",
    "=>",
)

SEPARATORS_DICT = {
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
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "**": "DOUBLE_STAR",
    "/": "SLASH",
    "//": "DOUBLE_SLASH",
    "%": "PERCENT",
    "+=": "PLUS_EQUAL",
    "++": "PLUS_PLUS",
    "--": "MINUS_MINUS",
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
    "->": "RETURN_TYPE_ARROW",
    "=>": "FUNCTION_ARROW",
}

FOLLOWERS = ("=", ">", "<", "+", "*", "-")

INT_PATTERN = re.compile(r"[+-]{0,1}\d+([eE][+-]{0,1}\d+){0,1}")

FLOAT_PATTERN = re.compile(
    r"[+-]{0,1}\d+[.]\d*([eE][+-]{0,1}\d+){0,1}|[+-]{0,1}\d*[.]\d+([eE][+-]{0,1}\d+){0,1}"
)

NUMBER_PATTERN = re.compile(FLOAT_PATTERN.pattern + "|" + INT_PATTERN.pattern)

STRING_PATTERN = re.compile(r'f{0,1}".*?(?<!\\)"')

INDENT_PATTERN = re.compile(r"[ ]{4}|[\t]")  # 4 consecutive spaces or a single tab

NAME_PATTERN = re.compile(r"[_a-zA-Z][_a-zA-Z0-9]*")

SEPARATOR_PATTERN = re.compile(
    r";|"
    r":|"
    r",|"
    r"\[|"
    r"]|"
    r"{|"
    r"}|"
    r"\(|"
    r"\)|"
    r":=|"
    r"=|"
    r"->|"
    r"-|"
    r"\*{1,2}|"
    r"/{1,2}|"
    r"%|"
    r"\+{1,2}|"
    r"--|"
    r"\+=|"
    r"~|"
    r"&|"
    r"[|]|"
    r"<<|"
    r">>|"
    r"<|"
    r"<=|"
    r">|"
    r">=|"
    r"==|"
    r"!=|"
    r"->|"
    r"=>"
)
