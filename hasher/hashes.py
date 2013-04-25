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
import os
import re
import sys


FORMAT_ERROR = 'MISFORMATTED'
HASH_ERROR = 'FAILED'
READ_ERROR = 'FAILED open or read'
SUCCESS = 'OK'
EXCLUDES = ('base.py', '__init__.py')
PATH = os.path.dirname(__file__)
PYEXT = '.py'
STATUS_MSG = '{0}: {1}\n'
CHECK_RE = re.compile(r'^([a-f0-9]+) (\*| )(.+)$')


class Hasher(object):
    """
    Base class for various sub-classes that implement specific hashing
    algorithms.
    """
    def __init__(self):
        self.chunk_size = 64 * 2048

    def _open_file(self, fname):
        if fname == '-':
            return sys.stdin
        return open(fname)

    def calculate_hash(self, file_object):
        """
        Calculate a hash value for the data in ``file_object
        """
        hasher = self.hashlib()
        for chunk in self.iterchunks(file_object):
            hasher.update(chunk)
        return hasher.hexdigest()

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

            if self.calculate_hash(check_f) == hash_value:
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
        hash_value = self.calculate_hash(fobj)
        return GenerateHashResult(self.name, fname, hash_value)

    def iterchunks(self, file_object):
        data = file_object.read(self.chunk_size)
        while data != '':
            yield data
            data = file_object.read(self.chunk_size)


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
                    '{0}: {1}: No such file or directory\n'.format(
                        self.name, result[0]
                        ))
            elif result[1] == HASH_ERROR and not status:
                sys.stdout.write(STATUS_MSG.format(*result))
            elif result[1] == FORMAT_ERROR and warn:
                sys.stderr.write(
                    '{0}: {1}: {2}: improperly formatted checksum'
                    ' line\n'.format(
                        self.name,
                        self.fname,
                        idx + 1,
                        ))

        if not status:
            if self.format_errors:
                sys.stderr.write(
                    '{0}: WARNING: {1} line{2} {3} improperly'
                    ' formatted\n'.format(
                        self.name,
                        self.format_errors,
                        's' if self.format_errors > 1 else '',
                        'are' if self.format_errors > 1 else 'is',
                        ))
            if self.read_errors:
                sys.stderr.write(
                    '{0}: WARNING: {1} listed file{2}'
                    ' could not be read\n'.format(
                        self.name,
                        self.read_errors,
                        's' if self.read_errors > 1 else '',
                        ))
            if self.hash_errors:
                sys.stderr.write(
                    '{0}: WARNING: {1} computed checksum{2}'
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


def hasher_factory(algorithm):
    klass = type("{0}Hasher".format(algorithm.upper()), (Hasher,), dict(
        name='{0}hash'.format(algorithm),
        hashlib=getattr(hashlib, algorithm),
        ))
    return klass()
