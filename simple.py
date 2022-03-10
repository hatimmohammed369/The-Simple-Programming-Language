#!/usr/local/bin/python3.10
if __name__ == "__main__":
    from argparse import ArgumentParser
    from tokenizer import Tokenizer
    from syntax_analyzer import SyntaxAnalyzer

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

    analyzer = SyntaxAnalyzer(tokenizer_object=tokenizer).analyze()
