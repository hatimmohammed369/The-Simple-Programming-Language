#!/usr/local/bin/python3.10
if __name__ == "__main__":
    from argparse import ArgumentParser
    from sys import argv
    from tokenizer import *
    from syntax_analyzer import *

    parser = ArgumentParser()

    parser.add_argument("--source", help="A small code sample to execute")
    parser.add_argument("--file", help="Source file")
    parser.add_argument(
        "--tabs",
        help="Indent using tabs",
        action="store_true",  # when --tabs option is supplied, it's true
        default=False,
    )
    parser.add_argument(
        "--spaces",
        help="Indent using spaces",
        action="store_true",  # when --spaces option is supplied, it's true
        default=True,
    )
    parser.add_argument(
        "--indent_size", help="Indent size", default=4
    )  # this means one indent token equals 4 spaces/tabs
    parser.add_argument("--tab_size", help="Tab size in spaces", default=4)

    args = parser.parse_args()

    # Source code
    if args.file:
        with open(args.file, "r") as source_file:
            source = str(source_file.read())
    else:
        source = args.source

    # Tab size
    if args.tab_size:
        tab = args.tab_size
    else:
        tab = 4

    # Indent type
    if "--tabs" in argv and "--spaces" in argv:
        raise ValueError("Use either --tabs or --spaces, not both")

    indent = " "
    if "--tabs" in argv:
        indent = "\t"

    # Indent size
    if args.indent_size:
        size = args.indent_size
    else:
        size = 4

    tokenizer = Tokenizer(
        text=source, indent_type=indent, indent_size=size, tab_size=tab
    )

    SyntaxAnalyzer(tokenizer).analyze()
