#!/usr/local/bin/python3.10

from tokenizer import *


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
