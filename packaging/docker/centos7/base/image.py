#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

if __name__ != "__main__":
    print("This script is not a module and is meant to be executed!", file=sys.stderr)
    exit(1)

# Add contents of 'docker' folder to our path so we can import stuff from util
sys.path.insert(0, Path(__file__, "..", "..", "..").resolve().as_posix())
try:
    from util import Container, Parser
except ImportError:
    raise


def main():
    # Init arg parser and add arguments if needed
    parser = Parser()
    args = parser.parse_args()

    # Init container helper
    container = Container(__file__, args.tag)

    if args.action == "build":
        container.build()
    elif args.action == "push":
        container.push()
    else:
        raise NotImplementedError("Unknown action: {}".format(args.action))

    return 0


exit(main())
