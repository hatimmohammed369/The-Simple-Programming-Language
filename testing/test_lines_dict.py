# Testing the whole tokenization process

from unittest import TestCase, main
from sys import path

path.append("/home/hatim/Desktop/The-Simple-Programming-Language/simple.py")

from simple import Tokenizer

if __name__ == "__main__":
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

    tokenizer = Tokenizer(source)

    for token in tokenizer:
        print(token)
