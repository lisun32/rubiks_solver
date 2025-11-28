import argparse
from . import __version__

def main(argv=None):
    parser = argparse.ArgumentParser(prog="rubiks-solver")
    parser.add_argument("--version", action="store_true", help="print version")
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)

if __name__ == "__main__":
    main()
