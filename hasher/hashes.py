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

import functools
import hashlib
import logging
import os
import re
import sys

from cliff import command

from hasher import __version__


FORMAT_ERROR = 'MISFORMATTED'
HASH_ERROR = 'FAILED'
READ_ERROR = 'FAILED open or read'
SUCCESS = 'OK'
EXCLUDES = ('base.py', '__init__.py')
PATH = os.path.dirname(__file__)
PYEXT = '.py'
STATUS_MSG = 'hasher {0}: {1}\n'
CHECK_RE = re.compile(r'^([a-f0-9]+) (\*| )(.+)$')


class Hasher(command.Command):
    """
    Base class for various sub-classes that implement specific hashing
    algorithms.
    """

    log = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super(Hasher, self).__init__(*args, **kwargs)
        self.chunk_size = 64 * 2048

    def _calculate_hash(self, file_object):
        """
        Calculate a hash value for the data in ``file_object
        """
        hasher = self.hashlib()
        for chunk in self.iterchunks(file_object):
            hasher.update(chunk)
        return hasher.hexdigest()

    def _open_file(self, fname):
        if fname == '-':
            return sys.stdin
        return open(fname)

    def check_hash(self, fname):
        """
        Check the hashed values in files against the calculated values

        Returns a list and a tuple of error counts.

        list: [(fname, 'OK' or 'FAILED' or 'FAILED open or read'),...]
        Error counts: (format_erros, hash_errors, read_errors)
        """
        fobj = self._open_file(fname)

        results = []
        format_errors = 0
        hash_errors = 0
        read_errors = 0
        for line in fobj:
            # remove any newline characters
            m = CHECK_RE.match(line.strip())
            if not m:
                results.append((None, FORMAT_ERROR))
                format_errors += 1
                continue
            hash_value, binary, check_file = m.groups()

            if binary == '*':
                mode = 'rb'
            else:
                mode = 'r'

            try:
                check_f = open(check_file, mode)
            except IOError:
                results.append((check_file, READ_ERROR))
                read_errors += 1
                continue

            if self._calculate_hash(check_f) == hash_value:
                results.append((check_file, SUCCESS,))
            else:
                results.append((check_file, HASH_ERROR,))
                hash_errors += 1
        return CheckHashResult(self.name, fname, *results, **dict(
            format_errors=format_errors,
            hash_errors=hash_errors,
            read_errors=read_errors,
            ))

    def generate_hash(self, fname):
        """Generate hashes for files"""
        fobj = self._open_file(fname)
        hash_value = self._calculate_hash(fobj)
        return GenerateHashResult(self.name, fname, hash_value)

    def get_parser(self, prog_name):
        parser = super(Hasher, self).get_parser(prog_name)
        parser.add_argument(
            "file",
            nargs="*",
            default="-",
            metavar="FILE",
            )

        parser.add_argument(
            "-c", "--check",
            action="store_true",
            help="read MD5 sums from the FILEs and check them",
            )

        parser.add_argument(
            "-b", "--binary",
            action="store_true",
            help="read in binary mode",
            )

        parser.add_argument(
            "-t", "--text",
            action="store_true",
            help="read in text mode (default)",
            )

        parser.add_argument(
            "--quiet",
            action="store_true",
            help="don't print OK for each successfully verified file",
            )

        parser.add_argument(
            "--status",
            action="store_true",
            help="don't output anything, status code shows success",
            )

        parser.add_argument(
            "-w", "--warn",
            action="store_true",
            help="warn about improperly formatted checksum lines",
            )

        parser.add_argument(
            "--strict",
            action="store_true",
            help="with --check, exit non-zero for any invalid input",
            )

        parser.add_argument(
            "--version",
            action="version",
            version="{0}.{1}.{2}{3}".format(*__version__),
            )

        parser.add_argument(
            '--debug',
            action='store_true',
            help='Show debugging statements',
            )

        return parser

    def iterchunks(self, file_object):
        data = file_object.read(self.chunk_size)
        while data != '':
            yield data
            data = file_object.read(self.chunk_size)

    def take_action(self, parsed_args):
        if parsed_args.check and (parsed_args.binary and parsed_args.text):
            self.log.error(
                'the --binary and --text options are meaningless when'
                ' verifying checksums')

        if not parsed_args.check and (
                parsed_args.warn or
                parsed_args.status or
                parsed_args.quiet or
                parsed_args.strict):
            self.log.error(
                'the --warn, --status, and --quiet options are meaningful'
                ' only when verifying checksums')

        for fname in parsed_args.file:
            if parsed_args.check:
                self.check_hash(fname).display(**vars(parsed_args))
            else:
                self.generate_hash(fname).display(**vars(parsed_args))


class HashResult(object):
    """
    Wrapper class for storing results of hashing operations
    """

    def __init__(self, name, fname):
        super(HashResult, self).__init__()
        self.name = name
        self.fname = fname

    def display(self, **kwargs):
        raise NotImplementedError()


@functools.total_ordering
class CheckHashResult(HashResult):
    """
    Result of checking hashes from a file
    """

    def __init__(self, name, fname, *args, **kwargs):
        super(CheckHashResult, self).__init__(name, fname)
        self.results = args
        self.format_errors = kwargs.get('format_errors', 0)
        self.hash_errors = kwargs.get('hash_errors', 0)
        self.read_errors = kwargs.get('read_errors', 0)

    def __eq__(self, other):
        return (
            (self.name.lower(), self.fname.lower(), self.results,
                self.format_errors, self.hash_errors, self.read_errors) ==
            (other.name.lower(), other.fname.lower(), other.results,
                other.format_errors, other.hash_errors, other.read_errors)
            )

    def __lt__(self, other):
        return (
            (self.name.lower(), self.fname.lower(), self.results,
                self.format_errors, self.hash_errors, self.read_errors) <
            (other.name.lower(), other.fname.lower(), other.results,
                other.format_errors, other.hash_errors, other.read_errors)
            )

    def __repr__(self):
        return (
            '<{0} ({1}, {2}, {3}, format_errors={4}, hash_errors={5},'
            ' read_errors={6})'.format(
                self.__class__.__name__,
                self.name,
                self.fname,
                self.results,
                self.format_errors,
                self.hash_errors,
                self.read_errors,
                ))

    def __str__(self):
        return (
            '({0}, {1}, {2}, format_errors={3}, hash_errors={4},'
            ' read_errors={5})'.format(
                self.name,
                self.fname,
                self.results,
                self.format_errors,
                self.hash_errors,
                self.read_errors,
                ))

    def display(self, **kwargs):
        status = kwargs.get('status', False)
        quiet = kwargs.get('quiet', False)
        warn = kwargs.get('warn', False)

        for idx, result in enumerate(self.results):
            if result[1] == SUCCESS and not (status or quiet):
                # display OK if not warn or status
                sys.stdout.write(STATUS_MSG.format(*result))
            elif result[1] == READ_ERROR:
                # display read errors
                if not status:
                    sys.stdout.write(STATUS_MSG.format(*result))
                sys.stderr.write(
                    'hasher {0}: {1}: No such file or directory\n'.format(
                        self.name, result[0]
                        ))
            elif result[1] == HASH_ERROR and not status:
                sys.stdout.write(STATUS_MSG.format(*result))
            elif result[1] == FORMAT_ERROR and warn:
                sys.stderr.write(
                    'hasher {0}: {1}: {2}: improperly formatted checksum'
                    ' line\n'.format(
                        self.name,
                        self.fname,
                        idx + 1,
                        ))

        if not status:
            if self.format_errors:
                sys.stderr.write(
                    'hasher {0}: WARNING: {1} line{2} {3} improperly'
                    ' formatted\n'.format(
                        self.name,
                        self.format_errors,
                        's' if self.format_errors > 1 else '',
                        'are' if self.format_errors > 1 else 'is',
                        ))
            if self.read_errors:
                sys.stderr.write(
                    'hasher {0}: WARNING: {1} listed file{2}'
                    ' could not be read\n'.format(
                        self.name,
                        self.read_errors,
                        's' if self.read_errors > 1 else '',
                        ))
            if self.hash_errors:
                sys.stderr.write(
                    'hasher {0}: WARNING: {1} computed checksum{2}'
                    ' did NOT match\n'.format(
                        self.name,
                        self.hash_errors,
                        's' if self.hash_errors > 1 else '',
                        ))


@functools.total_ordering
class GenerateHashResult(HashResult):
    """
    Result of calculating a hash for a file
    """

    def __init__(self, name, fname, hash_value):
        super(GenerateHashResult, self).__init__(name, fname)
        self.hash = hash_value

    def __eq__(self, other):
        return (
            (self.name.lower(), self.fname.lower(), self.hash.lower()) ==
            (other.name.lower(), other.fname.lower(), other.hash.lower())
            )

    def __lt__(self, other):
        return (
            (self.name.lower(), self.fname.lower(), self.hash.lower()) <
            (other.name.lower(), other.fname.lower(), other.hash.lower())
            )

    def __repr__(self):
        return '<{0} ({1}, {2}, {3})>'.format(
            self.__class__,
            self.name,
            self.fname,
            self.hash_value,
            )

    def __str__(self):
        return (self.name, self.fname, self.hash_value)

    def display(self, **kwargs):
        binary = kwargs.get('binary', False)

        line = '{0} {2}{1}\n'.format(
            self.hash,
            self.fname,
            '*' if binary else ' ',
            )

        if '//' in line:
            line = '//' + line.replace('//', '////')
        sys.stdout.write(line)


class MD5Hasher(Hasher):
    name = 'md5'
    hashlib = hashlib.md5


class SHA1Hasher(Hasher):
    name = 'sha1'
    hashlib = hashlib.sha1


class SHA256Hasher(Hasher):
    name = 'sha256'
    hashlib = hashlib.sha256
