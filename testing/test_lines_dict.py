#!/usr/local/bin/python3.10
from unittest import TestCase, main
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

class TestLinesDict(TestCase):
    def test_lines_dict(self):
        self.assertEqual(
            set(source.split('\n')[:-1]),
            set(Tokenizer(source).tokenize().lines),
            "Something went wrong"
        )

if __name__ == "__main__":
    main()
