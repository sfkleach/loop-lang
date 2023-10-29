import argparse
from typing import Callable, Dict, Union, Tuple, List, cast
import io
import sys
from looplang import StopLoopLang, execute

def main():
    argsp = argparse.ArgumentParser()
    argsp.add_argument('-f', '--file', type=argparse.FileType('r'), default=sys.stdin, help='LOOP code')
    argsp.add_argument('-S', '--sugar', action='store_true', help='enable syntactic sugar')
    argsp.add_argument('-N', '--enhanced', action='store_true', help='enable ERROR enhancement')
    argsp.add_argument('-e', '--execute', type=str, default=None, help='Semi-colon separated initial statements to execute')
    argsp.add_argument('-p', '--print', type=str, default=None, help='Comma-separated list of registers to print')
    args = argsp.parse_args()

    state: Dict[str, int] = {}
    try:
        if args.execute is not None:
            execute(io.StringIO(args.execute), state, sugar=args.sugar, enhanced=args.enhanced)
        execute(args.file, state, sugar=args.sugar, enhanced=args.enhanced)
        for a in args.print.split(',') if args.print else state.keys():
            print(a, '=', state[a])
    except StopLoopLang:
        sys.exit(1)

if __name__ == "__main__":
    main()
