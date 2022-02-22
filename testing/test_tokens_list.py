#!/usr/local/bin/python3.10
from unittest import TestCase, main, TextTestRunner, TestLoader
from sys import path

path.append("/home/hatim/Desktop/The-Simple-Programming-Language")

from simple import Tokenizer

from argparse import ArgumentParser

parser = ArgumentParser()

parser.add_argument("-s", "--source", help="A small code sample to execute")
parser.add_argument("-f", "--file", help="Source file")

args = parser.parse_args()

if args.file:
    with open(args.file, "r") as source_file:
        source = str(source_file.read())
else:
    source = args.source


class TestTokensList(TestCase):
    def test_tokens_list(self):
        print("Source preview:")
        with open("/tmp/for_cat", "w") as tmp:
            tmp.write(source)
        from os import system

        system("cat /tmp/for_cat -n")
        tokenizer = Tokenizer(source).tokenize()
        tokens_list, lines = tokenizer.tokens_list, tokenizer.lines
        print(f"Tokens list:\n{tokens_list}")
        for token in tokens_list:
            # First test if token pos attribute is correct
            # Use idx for now
            begin, end = token.begin, token.end
            self.assertEqual(
                str(
                    token.value
                ),  # because when Token represents a number, token.value is also
                source[begin.idx : end.idx],
                "Token {token} has idx position incorrectly recored\n{begin.idx = }\n{end.idx = }",
            )

        # now test using lines
        for token in tokens_list:
            if token.value != "\n":
                ln, col_begin, col_end = token.begin.ln, token.end.col, token.end.col
                self.assertEqual(
                    str(
                        token.value
                    ),  # because when Token represents a number, token.value is also
                    lines[ln].value[col_begin:col_end],
                    f"Something wrong will col attributes"
                    + f"\n{token = }\n{lines[ln] = }\n{lines[ln].value[col_begin:col_end] = }\n",
                )


if __name__ == "__main__":
    TextTestRunner().run(TestLoader().loadTestsFromTestCase(TestTokensList))
