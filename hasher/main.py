'''
Created on Feb 6, 2013

@author: wscheper
'''
import argparse
import importlib

from .version import __version__


DESCRIPTION = """
Print or check MD5 (128-bit) checksums.
With no FILE, or when FILE is -, read standard input.
"""
EPILOG = """
The sums are computed as described in RFC 1321.  When checking, the input
should be a former output of this program.  The default mode is to print
a line with checksum, a character indicating type (`*" for binary, ` " for
text), and name for each FILE.
"""


def main():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, epilog=EPILOG)

    parser.add_argument(
        "file",
        nargs="*",
        default="-",
        metavar="FILE")

    parser.add_argument(
        "-c", "--check",
        action="store_true",
        help="read MD5 sums from the FILEs and check them")

    parser.add_argument(
        "-b", "--binary",
        action="store_true",
        default=False,
        help="read in binary mode")

    parser.add_argument(
        "-t", "--text",
        action="store_true",
        default=True,
        help="read in text mode (default)")

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="don't print OK for each successfully verified file")

    parser.add_argument(
        "--status",
        action="store_true",
        help="don't output anything, status code shows success")

    parser.add_argument(
        "-w", "--warn",
        action="store_true",
        help="warn about improperly formatted checksum lines")

    parser.add_argument(
        "--strict",
        action="store_true",
        help="with --check, exit non-zero for any invalid input")

    parser.add_argument(
        "--version",
        action="version",
        version=".".join(map(str, __version__)))

    args = parser.parse_args()
    if args.check and (args.binary or args.text):
        parser.error(
            'the --binary and --text options are meaningless when verifying'
            'checksums')

    if not args.check and (args.warn or args.status or args.quiet):
        parser.error(
            'the --warn, --status, and --quiet options are meaningful'
            ' only when verifying checksums')

    module = importlib.import_module("hasher.hashes.%s" % parser.prog[:-3])
    module.run(args)

if __name__ == '__main__':
    main()
