"""
Command line parser for md5sum utility
"""
import argparse

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

md5_parser = argparse.ArgumentParser(
    description=DESCRIPTION, epilog=EPILOG)
md5_parser.add_argument("FILE", nargs="*", default="-")
md5_parser.add_argument("-c", "--check", action="store_true",
                        help="read MD5 sums from the FILEs and check them")
md5_parser.add_argument("-b", "--binary", dest="is_text",
                        action="store_false", help="read in binary mode")
md5_parser.add_argument("-t", "--text", dest="is_text", action="store_true",
                        default=True, help="read in text mode (default)")
md5_parser.add_argument("--quiet", action="store_true",
                        help="don't print OK for each successfully verified"
                        " file")
md5_parser.add_argument("--status", action="store_true",
                        help="don't output anything, status code shows"
                        " success")
md5_parser.add_argument("-w", "--warn", action="store_true",
                        help="warn about improperly formatted checksum lines")
md5_parser.add_argument("--strict", action="store_true",
                        help="with --check, exit non-zero for any invalid"
                        " input")
md5_parser.add_argument("--version", action="version",
                        version=".".join(map(str, __version__)))
