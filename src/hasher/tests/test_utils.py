import hashlib

from ..utils import check_re


class TestCheckRegex(object):
    '''Test the regex used to parse check files'''

    def setup_method(self, method):
        self.filename = 'myfile.txt'
        self.md5_hash = hashlib.md5('This is a test string').hexdigest()

    def test_valid_string(self):
        string = '%s  %s' % (self.filename, self.md5_hash)
        match = check_re.match(string)

        assert match is not None
        assert match.groups() == (self.filename, None, self.md5_hash)

    def test_binary_string(self):
        string = '%s  *%s' % (self.filename, self.md5_hash)
        match = check_re.match(string)

        assert match is not None
        assert match.groups() == (self.filename, '*', self.md5_hash)
