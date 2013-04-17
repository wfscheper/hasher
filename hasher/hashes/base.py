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

import re
import sys

from hasher import FORMAT_ERROR, HASH_ERROR, READ_ERROR, SUCCESS


check_re = re.compile(r'^([a-f0-9]+)  (\*)?(.+)$')


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
        for chunk in self.iterchunks(file_object):
            self.hashlib.update(chunk)
        return self.hashlib.hexdigest()

    def check_hash(self, fname):
        """
        Check the hashed values in files against the calculated values

        Returns a list and a tuple of error counts.

        list: [(fname, 'OK' or 'FAILED' or 'FAILED open or read'),...]
        Error counts: (format_erros, hash_errors, read_errors)
        """
        fobj = self._open_file(fname)

        results = CheckHashResult(self.name, fname)
        for line in fobj:
            # remove any newline characters
            m = check_re.match(line.strip())
            if not m:
                results.append((None, FORMAT_ERROR))
                results.format_errors += 1
                continue
            hash_value, binary, check_file = m.groups()

            if binary == '*':
                mode = 'rb'
            else:
                mode = 'r'

            try:
                check_f = open(check_file, mode)
            except IOError:
                results.read_errors += 1
                results.append((fname, READ_ERROR))
                continue

            if self.calculate_hash(check_f) == hash_value:
                results.append((fname, SUCCESS,))
            else:
                results.append((fname, HASH_ERROR,))
                results.hash_errors += 1
        return results

    def generate_hash(self, fname):
        """Generate hashes for files"""
        fobj = self._open_file(fname)
        hash_value = self.calculate_hash(fobj)
        return GenerateHashResult(self.name, fname, hash_value)

    def iterchunks(self, file_object):
        data = file_object.read(self.chunk_size)
        while data:
            yield data
            data = file_object.read(self.chunk_size)


class HashResult(list):

    def __init__(self, name, fname, *args):
        super(HashResult, self).__init__(args)
        self.name = name
        self.fname = fname

    def display(self, **kwargs):
        raise NotImplementedError()


class CheckHashResult(HashResult):

    def __init__(self, name, fname, *args, **kwargs):
        super(CheckHashResult, self).__init__(name, fname, *args)
        self.format_errors = kwargs.get('format_errors', 0)
        self.hash_errors = kwargs.get('hash_errors', 0)
        self.read_errors = kwargs.get('read_errors', 0)

    def display(self, **kwargs):
        status = kwargs.get('status', False)
        quiet = kwargs.get('quiet', False)
        warn = kwargs.get('warn', False)

        for idx, result in enumerate(self):
            if result[1] == 'FAILED open or read':
                sys.stderr.write(
                    '{0}: {1}: No such file or directory\n'.format(
                        self.name, result[0]
                        ))
            if not (status or quiet) and result != (None, FORMAT_ERROR):
                sys.stdout.write('{0}: {1}\n'.format(*result))

            if warn and result == (None, FORMAT_ERROR):
                sys.stderr.write(
                    '{0}: {1}: {2}: improperly formatted checksum'
                    ' line\n'.format(
                        self.name,
                        self.fname,
                        idx + 1,
                        ))

        if not status:
            if warn and self.format_errors:
                sys.stderr.write(
                    '{0}: WARNING: {1} line{2} is improperly'
                    ' formatted\n'.format(
                        self.name,
                        self.format_errors,
                        's' if self.format_errors > 1 else '',
                        ))
            if self.read_errors:
                sys.stderr.write(
                    '{0}: WARNING: {1} listed file{2} could not be read\n'.format(
                        self.name,
                        self.read_errors,
                        's' if self.read_errors > 1 else '',
                        ))
            if self.hash_errors:
                sys.stderr.write(
                    '{0}: WARNING: {1} computed checksum{2} did NOT match\n'.format(
                        self.name,
                        self.hash_errors,
                        's' if self.hash_errors > 1 else '',
                        ))


class GenerateHashResult(HashResult):

    def display(self, **kwargs):
        binary = kwargs.get('binary', False)

        line = '{0} {2}{1}\n'.format(self[0], self[1], '*' if binary else '')

        if '//' in line:
            line = '//' + line.replace('//', '////')
        sys.stdout.write(line)
