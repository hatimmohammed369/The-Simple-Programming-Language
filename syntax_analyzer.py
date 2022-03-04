#!/usr/local/bin/python3.10

# File syntax_analyzer.py
# Perform syntax analysis, in other words, check if given source code is syntactically correct

from argparse import ArgumentParser
from tokenizer import Tokenizer, Token


class SyntaxAnalyzer:
    def __init__(self, tokenizer_object: Tokenizer):
        if not tokenizer_object.done:
            tokenizer_object.tokenize()
        self.tokenizer: Tokenizer = tokenizer_object
        self.done = False  # becomes True after analyze(self) is done

    def analyze(self):
        for token in self.tokenizer:
            pass
        self.done = True
        return self


if __name__ == "__main__":

    parser = ArgumentParser()

    parser.add_argument("-s", "--source", help="A small code sample to execute")
    parser.add_argument("-f", "--file", help="Source file")

    args = parser.parse_args()

    if args.file:
        with open(args.file, "r") as source_file:
            source = str(source_file.read())
    else:
        source = args.source

    SyntaxAnalyzer(Tokenizer(source)).analyze()
