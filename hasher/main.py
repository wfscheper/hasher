# Copyright 2013 Walter Scheper
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Created on Feb 6, 2013

@author: wscheper
'''
import sys

from hasher.parser import parser
from hasher.hashes import hasher_factory


def main(argv=None):
    args = parser.parse_args(argv)
    if args.check and (args.binary and args.text):
        parser.error(
            'the --binary and --text options are meaningless when verifying'
            ' checksums')

    if not args.check and (
            args.warn or args.status or args.quiet or args.strict):
        parser.error(
            'the --warn, --status, and --quiet options are meaningful'
            ' only when verifying checksums')

    hasher = hasher_factory(parser.prog.rpartition('hash')[0])

    try:
        for fname in args.file:
            if args.check:
                hasher.check_hash(fname).display(**vars(args))
            else:
                hasher.generate_hash(fname).display(**vars(args))
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        if args.debug:
            raise
        sys.stderr.write(e.args[0] + '\n')
        return 1
    return 0

if __name__ == '__main__':
    main()
