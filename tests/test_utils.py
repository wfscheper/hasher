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

import hashlib

from hasher.hashes.base import check_re


class TestCheckRegex(object):
    '''Test the regex used to parse check files'''

    def setup_method(self, method):
        self.filename = 'myfile.txt'
        self.hash = hashlib.md5('This is a test string').hexdigest()

    def test_valid_string(self):
        string = '%s  %s' % (self.hash, self.filename)
        match = check_re.match(string)

        assert match is not None
        assert match.groups() == (self.hash, None, self.filename)

    def test_binary_string(self):
        string = '%s  *%s' % (self.hash, self.filename)
        match = check_re.match(string)

        assert match is not None
        assert match.groups() == (self.hash, '*', self.filename)

    def test_missing_hash(self):
        string = "{hash} ".format(hash=self.hash)
        assert check_re.match(string) is None

    def test_missing_filename(self):
        string = "  {file}".format(file=self.filename)
        assert check_re.match(string) is None

    def test_missing_flag(self):
        string = "{hash} {file}".format(hash=self.hash, file=self.filename)
        assert check_re.match(string) is None

    def test_wrong_flag(self):
        string = "{hash} +{file}".format(hash=self.hash, file=self.filename)
        assert check_re.match(string) is None

    def test_filename_with_slash(self):
        filename = "filewith\\slash.txt"
        string = "{hash}  {file}".format(hash=self.hash, file=filename)
        match = check_re.match(string)
        assert match is not None
        assert match.groups() == (self.hash, None, filename)

    def test_filename_with_space(self):
        filename = "filewith space.txt"
        string = "{hash}  {file}".format(hash=self.hash, file=filename)
        match = check_re.match(string)
        assert match is not None
        assert match.groups() == (self.hash, None, filename)
