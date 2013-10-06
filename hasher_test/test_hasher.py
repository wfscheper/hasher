'''
Created on Feb 8, 2013

@author: wscheper
'''
import hashlib
import unittest
from StringIO import StringIO

from mock import (
    patch,
    MagicMock,
    call,
    )
import pytest

from hasher import hashes
from hasher.hashes import (
    CHECK_RE,
    FORMAT_ERROR,
    HASH_ERROR,
    READ_ERROR,
    SUCCESS,
    )


class TestCheckRegex(object):
    '''Test the regex used to parse check files'''

    def setup_method(self, method):
        self.filename = 'myfile.txt'
        self.hash = hashlib.md5('This is a test string').hexdigest()

    def test_valid_string(self):
        string = '%s  %s' % (self.hash, self.filename)
        match = CHECK_RE.match(string)

        assert match is not None
        assert match.groups() == (self.hash, ' ', self.filename)

    def test_binary_string(self):
        string = '%s *%s' % (self.hash, self.filename)
        match = CHECK_RE.match(string)

        assert match is not None
        assert match.groups() == (self.hash, '*', self.filename)

    def test_missing_hash(self):
        string = "{hash} ".format(hash=self.hash)
        assert CHECK_RE.match(string) is None

    def test_missing_filename(self):
        string = "  {file}".format(file=self.filename)
        assert CHECK_RE.match(string) is None

    def test_missing_flag(self):
        string = "{hash} {file}".format(hash=self.hash, file=self.filename)
        assert CHECK_RE.match(string) is None

    def test_wrong_flag(self):
        string = "{hash} +{file}".format(hash=self.hash, file=self.filename)
        assert CHECK_RE.match(string) is None

    def test_filename_with_slash(self):
        filename = "filewith\\slash.txt"
        string = "{hash}  {file}".format(hash=self.hash, file=filename)
        match = CHECK_RE.match(string)
        assert match is not None
        assert match.groups() == (self.hash, ' ', filename)

    def test_filename_with_space(self):
        filename = "filewith space.txt"
        string = "{hash}  {file}".format(hash=self.hash, file=filename)
        match = CHECK_RE.match(string)
        assert match is not None
        assert match.groups() == (self.hash, ' ', filename)


class TestMD5Hasher(unittest.TestCase):
    def setUp(self):
        self.data = 'a string of data to hash'
        self.data_md5 = '719231ebf10a82f0b9c29c26210a6ec3'
        self.md5hasher = hashes.hasher_factory('md5')

    @patch('hasher.hashes.sys')
    def test_basic_hash(self, _sys):
        _sys.stdin = MagicMock()
        _sys.stdin.read.side_effect = [self.data, '']

        expected_result = hashes.GenerateHashResult('md5hash', '-', self.data_md5)
        result = self.md5hasher.generate_hash('-')
        assert expected_result == result

    @patch('__builtin__.open')
    def test_generate_invalid_file(self, _open):
        _open.side_effect = IOError()

        with pytest.raises(IOError):
            self.md5hasher.generate_hash('md5hash')
        _open.assert_called_once_with('md5hash')

    @patch('hasher.hashes.sys')
    def test_generate_display_text(self, _sys):
        _sys.stdout = MagicMock(spec=file)

        hashes.GenerateHashResult(
            'md5hash',
            'foo',
            self.data_md5,
            ).display()
        _sys.stdout.write.assert_called_with(
            '%s  foo\n' % self.data_md5,
            )

    @patch('__builtin__.open')
    def test_check_data(self, _open):
        _open.side_effect = [
            StringIO(
                '%s  %s\n' % (self.data_md5, 'bar'),
                ),
            StringIO(self.data),
            ]

        result = self.md5hasher.check_hash('foo')
        expected_result = hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', SUCCESS),
            )
        assert expected_result == result
        assert 0 == result.format_errors
        assert 0 == result.hash_errors
        assert 0 == result.read_errors

    @patch('__builtin__.open')
    def test_check_readerror(self, _open):
        _open.side_effect = [
            StringIO(
                '%s  %s\n' % (self.data_md5, 'bar'),
                ),
            IOError(),
            ]

        result = self.md5hasher.check_hash('foo')
        expected_result = hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', READ_ERROR),
            read_errors=1,
            )

        assert expected_result == result
        assert 0 == result.format_errors
        assert 0 == result.hash_errors
        assert 1 == result.read_errors

    @patch('__builtin__.open')
    def test_check_mismatch(self, _open):
        _open.side_effect = [
            StringIO('%s  %s\n' % (self.data_md5, 'bar')),
            StringIO(self.data + 'md5hash'),
            ]

        result = self.md5hasher.check_hash('foo')
        expected_result = hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', HASH_ERROR),
            hash_errors=1,
            )
        assert expected_result == result
        assert 0 == result.format_errors
        assert 1 == result.hash_errors
        assert 0 == result.read_errors

    @patch('__builtin__.open')
    def test_check_formaterror(self, _open):
        _open.side_effect = [
            StringIO('%s +%s\n' % (self.data_md5, 'bar')),
            ]

        result = self.md5hasher.check_hash('foo')
        expected_result = hashes.CheckHashResult(
            'md5hash',
            'foo',
            (None, FORMAT_ERROR),
            format_errors=1,
            )
        assert expected_result == result
        assert 1 == result.format_errors
        assert 0 == result.hash_errors
        assert 0 == result.read_errors

    @patch('hasher.hashes.sys')
    def test_checkresult_display(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult('md5hash', 'foo', ('bar', SUCCESS)).display()
        expected_stdout_calls = [
            call('bar: OK\n'),
            ]
        assert expected_stdout_calls == _sys.stdout.write.call_args_list

    @patch('hasher.hashes.sys')
    def test_checkresult_display_formaterror(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult('md5hash', 'foo', format_errors=1).display()
        assert [] == _sys.stdout.write.call_args_list

        expected_stderr_calls = [
            call('md5hash: WARNING: 1 line is improperly formatted\n'),
            ]
        assert expected_stderr_calls == _sys.stderr.write.call_args_list

        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult('md5hash', 'foo', format_errors=2).display()
        assert [] == _sys.stdout.write.call_args_list

        expected_stderr_calls = [
            call('md5hash: WARNING: 2 lines are improperly formatted\n'),
            ]
        assert expected_stderr_calls == _sys.stderr.write.call_args_list

    @patch('hasher.hashes.sys')
    def test_checkresult_display_hasherror(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', HASH_ERROR),
            hash_errors=1,
            ).display()

        expected_stdout_calls = [
            call('bar: FAILED\n'),
            ]
        assert expected_stdout_calls == _sys.stdout.write.call_args_list

        expected_stderr_calls = [
            call('md5hash: WARNING: 1 computed checksum did NOT match\n'),
            ]
        assert expected_stderr_calls ==  _sys.stderr.write.call_args_list

        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', HASH_ERROR),
            ('baz', HASH_ERROR),
            hash_errors=2,
            ).display()

        expected_stdout_calls = [
            call('bar: FAILED\n'),
            call('baz: FAILED\n'),
            ]
        assert expected_stdout_calls ==  _sys.stdout.write.call_args_list

        expected_stderr_calls = [
            call('md5hash: WARNING: 2 computed checksums did NOT match\n'),
            ]
        assert expected_stderr_calls == _sys.stderr.write.call_args_list

    @patch('hasher.hashes.sys')
    def test_checkresult_display_readerror(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', READ_ERROR),
            read_errors=1,
            ).display()

        expected_stdout_calls = [
            call('bar: FAILED open or read\n'),
            ]
        assert expected_stdout_calls == _sys.stdout.write.call_args_list

        expected_stderr_calls = [
            call('md5hash: bar: No such file or directory\n'),
            call('md5hash: WARNING: 1 listed file could not be read\n'),
            ]
        assert expected_stderr_calls == _sys.stderr.write.call_args_list


    @patch('hasher.hashes.sys')
    def test_checkresult_display_readerror_multiple(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', READ_ERROR),
            ('baz', READ_ERROR),
            read_errors=2,
            ).display()

        expected_stdout_calls = [
            call('bar: FAILED open or read\n'),
            call('baz: FAILED open or read\n'),
            ]
        assert expected_stdout_calls == _sys.stdout.write.call_args_list

        expected_stderr_calls = [
            call('md5hash: bar: No such file or directory\n'),
            call('md5hash: baz: No such file or directory\n'),
            call('md5hash: WARNING: 2 listed files could not be read\n'),
            ]
        assert expected_stderr_calls == _sys.stderr.write.call_args_list

    @patch('hasher.hashes.sys')
    def test_checkresult_status(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', SUCCESS),
            ).display(status=True)

        assert [] == _sys.stdout.write.call_args_list
        assert [] == _sys.stderr.write.call_args_list

    @patch('hasher.hashes.sys')
    def test_checkresult_status_hasherror(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', SUCCESS),
            hash_errors=1,
            ).display(status=True)

        assert [] == _sys.stdout.write.call_args_list
        assert [] == _sys.stderr.write.call_args_list

    @patch('hasher.hashes.sys')
    def test_checkresult_status_readerror(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', READ_ERROR),
            read_errors=1,
            ).display(status=True)

        assert [] == _sys.stdout.write.call_args_list

        expected_stderr_calls = [
            call('md5hash: bar: No such file or directory\n'),
            ]
        assert expected_stderr_calls == _sys.stderr.write.call_args_list

    @patch('hasher.hashes.sys')
    def test_checkresult_strict(self, _sys):
        pass

    @patch('hasher.hashes.sys')
    def test_checkresult_warn(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', SUCCESS),
            ).display(warn=True)

        expected_stdout_calls = [
            call('bar: OK\n'),
            ]
        assert expected_stdout_calls == _sys.stdout.write.call_args_list
        assert [] == _sys.stderr.write.call_args_list

    @patch('hasher.hashes.sys')
    def test_checkresult_warn_formaterror(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', SUCCESS),
            (None, FORMAT_ERROR),
            format_errors=1,
            ).display(warn=True)

        expected_stdout_calls = [
            call('bar: OK\n'),
            ]
        assert expected_stdout_calls == _sys.stdout.write.call_args_list

        expected_stderr_calls = [
            call('md5hash: foo: 2: improperly formatted checksum line\n'),
            call('md5hash: WARNING: 1 line is improperly formatted\n'),
            ]
        assert expected_stderr_calls == _sys.stderr.write.call_args_list

    @patch('hasher.hashes.sys')
    def test_checkresult_quiet(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        hashes.CheckHashResult(
            'md5hash',
            'foo',
            ('bar', SUCCESS),
            ).display(quiet=True)

        assert [] == _sys.stdout.write.call_args_list
        assert [] == _sys.stdout.write.call_args_list


if __name__ == '__main__':
    unittest.main()
