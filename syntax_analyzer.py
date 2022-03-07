#!/usr/local/bin/python3.10

from tokenizer import *
from dataclasses import dataclass


@dataclass(init=True, repr=True)
class SyntaxToken:
    value: str
    next_expected: tuple[str]
    context: tuple[str]


CONTEXTS = (
    SyntaxToken("define", next_expected=("NAME",), context=("CONST_VAR_DEFINTION",)),
)


class SyntaxAnalyzer:
    def __init__(self, tokenizer_object: Tokenizer):
        self.tokenizer = tokenizer_object
        if self.tokenizer.done is False:
            self.tokenizer.tokenize()
        self.done = False  # becomes True after analyze() successfully execute

    def analyze(self):
        pass
        self.done = True
        return self


# End Of Class SyntaxAnalyzer
