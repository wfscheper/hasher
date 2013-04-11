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


check_re = re.compile(r'^([ a-f0-9]+)  (\*)?(.+)$')


class Hasher(object):
    """Base class for various sub-classes that implement specific hashing
    algorithms.
    """
    def __init__(self, args):
        self.args = args
        self.chunk_size = 64 * 2048

    def calculate_hash(self, file_object):
        """Calculate a hash value for the data in ``file_object
        """
        for chunk in self.iterchunks(file_object):
            self.hashlib.update(chunk)
        return self.hashlib.hexdigest()

    def check_hashes(self):
        """Check the hashed values in files against the calculated values
        """
        for fname, fobj in self.iterfiles():
            # if file failed to open, report that
            if fobj is None:
                self.report_failed_read(fname)
                continue

            read_errors = 0
            hash_errors = 0
            format_errors = 0

            for line in fobj:
                m = check_re.match(line)
                if not m:
                    format_errors += 1
                    continue
                check_file, binary, hash_value = m.groups()

                if binary == '*':
                    mode = 'rb'
                else:
                    mode = 'r'

                try:
                    check_f = open(check_file, mode)
                except IOError:
                    self.read_error(check_file)
                    self.report_failed_read(check_file)
                    read_errors += 1
                    continue

                if self.calculate_hash(check_f) == hash_value:
                    self.report_match(check_file)
                else:
                    self.report_mismatch(check_file)
                    hash_errors += 1

            self.report_format_errors(format_errors)
            self.report_read_errors(read_errors)
            self.report_hash_errors(hash_errors)

    def generate_hashes(self):
        """Generate hashes for files"""
        for fname, fobj in self.iterfiles():
            if fobj is not None:
                self.report_hash(fname, self.calculate_hash(fobj))

    def iterfiles(self):
        """Iterate over filenames in args.file"""
        for fname in self.args.FILE:
            if fname == '-':
                # read from stdin
                fobj = sys.stdin
            else:
                # try and open file
                try:
                    fobj = open(fname)
                except IOError:
                    self.read_error(fname)
                    fobj = None
            yield (fname, fobj)

    def iterchunks(self, file_object):
        data = file_object.read(self.chunk_size)
        while data:
            yield data
            data = file_object.read(self.chunk_size)

    def read_error(self, filename):
        """Write a warning that we couldn't open the file ``filename``
        """
        sys.stderr.write("{0}: {1}: No such file or directory\n".format(
            self.name, filename))

    def report_failed_read(self, filename):
        if not self.args.status:
            sys.stdout.write("{0}: FAILED open or read".format(filename))

    def report_format_errors(self, count):
        if not self.args.status and count:
            sys.stderr.write(
                "{0}: WARNING: {1} line{2} are improperly formatted\n".format(
                    self.name, count, 's' if count > 1 else ''))

    def report_hash(self, filename, hash_value):
        if not self.args.quiet:
            if self.args.binary:
                msg = "{0} *{1}\n"
            else:
                msg = "{0}  {1}\n"
            # format the message
            msg = msg.format(hash_value, filename)

            # append a \ to lines for files that contain any backslashes
            # and escape the backslashes
            if "\\" in filename:
                msg = "\\" + msg.replace("\\", "\\\\")
            sys.stdout.write(msg)

    def report_hash_errors(self, count):
        if not self.args.status and count:
            sys.stderr.write(
                "{0}: WARNING: {1} computed checksum{2} "
                "did NOT match\n".format(
                    self.name, count, 's' if count > 1 else ''))

    def report_match(self, filename):
        if not (self.args.quiet or self.args.status):
            sys.stdout.write('{0}: OK'.format(filename))

    def report_mismatch(self, filename):
        if not self.args.status:
            sys.stdout.write('{0}: FAILED'.format(filename))

    def report_read_errors(self, count):
        """Report the number of read errors encountered
        """
        if not self.args.status and count:
            sys.stderr.write(
                "{0}: WARNING: {1} listed file{2} could not be read\n".format(
                    self.name, count, 's' if count > 1 else ''))

    def run(self):
        if self.args.check:
            self.check_hashes()
        else:
            self.generate_hashes()
