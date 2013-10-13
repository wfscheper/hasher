'''
Created on Feb 8, 2013

@author: wscheper
'''
import argparse
import hashlib
import unittest
from StringIO import StringIO

from mock import (
    patch,
    MagicMock,
    call,
    )
import pytest

from hasher import (
    app,
    hashes,
    )


class TestMD5Hasher(unittest.TestCase):
    def setUp(self):
        self.app = app.HasherApp()
        self.data = 'a string of data to hash\n'
        self.check_data = (
            '3ac11b17fa463072f069580031317af2  AUTHORS\n'
            '4e6ee384b7a0a002681cda43a5ccc9d0  README.rst\n'
            )
        self.data_md5 = hashlib.md5(self.data).hexdigest()
        self.md5hasher = hashes.MD5Hasher(self.app, None)
        self.args = argparse.Namespace(
            binary=False,
            warn=False,
            status=False,
            quiet=False,
            )

    @patch('__builtin__.open')
    def test_generate_invalid_file(self, _open):
        _open.side_effect = IOError()

        with pytest.raises(IOError):
            self.md5hasher.generate_hash('foo', self.args)
        _open.assert_called_once_with('foo', 'r')

    @patch('__builtin__.open')
    def test_generate_display_text(self, _open):
        _open.return_value = StringIO(self.data)
        self.md5hasher.app.stdout = MagicMock(spec=file)

        self.md5hasher.generate_hash('foo', self.args)
        self.md5hasher.app.stdout.write.assert_called_with(
            '%s  foo\n' % self.data_md5,
            )

    @patch('__builtin__.open')
    def test_generate_display_text_binary(self, _open):
        _open.return_value = StringIO(self.data)
        self.md5hasher.app.stdout = MagicMock(spec=file)

        self.args.binary = True
        self.md5hasher.generate_hash('foo', self.args)
        self.md5hasher.app.stdout.write.assert_called_with(
            '%s *foo\n' % self.data_md5,
            )

    @patch('__builtin__.open')
    def test_checkresult_display(self, _open):
        _open.side_effect = [
            StringIO(self.check_data),
            StringIO('AUTHORS\n'),
            StringIO('README.rst\n'),
            ]
        self.md5hasher.app.stdout = MagicMock(spec=file)
        self.md5hasher.app.stderr = MagicMock(spec=file)

        rc = self.md5hasher.check_hash('foo', self.args)
        expected_stdout_calls = [
            call('AUTHORS: OK\n'),
            call('README.rst: OK\n'),
            ]
        assert (expected_stdout_calls ==
                self.md5hasher.app.stdout.write.call_args_list)
        assert rc == 0

    @patch('__builtin__.open')
    def test_checkresult_display_formaterror(self, _open):
        _open.side_effect = [
            StringIO(
                '1234  File\n'
                '1111111111111111111111111111111  File2\n'
                'f2cd884501b6913cad2ae243475a75d3 +README.rst\n'
                '111111111111111111111111111111111  File2\n'
                '1111111111111111111111111111111111  File2\n'
                ),
            ]
        self.md5hasher.app.stdout = MagicMock(spec=file)
        self.md5hasher.app.stderr = MagicMock(spec=file)

        rc = self.md5hasher.check_hash('foo', self.args)

        assert [] == self.md5hasher.app.stdout.write.call_args_list

        expected_stderr_calls = [
            call('hasher md5: WARNING: 5 lines are improperly formatted\n'),
            ]
        assert (expected_stderr_calls ==
                self.md5hasher.app.stderr.write.call_args_list)
        assert rc == 1

    @patch('__builtin__.open')
    def test_checkresult_display_hasherror(self, _open):
        _open.side_effect = [
            StringIO(self.check_data),
            StringIO('AUTHORS.\n'),
            StringIO('README.rst\n'),
            ]
        self.md5hasher.app.stdout = MagicMock(spec=file)
        self.md5hasher.app.stderr = MagicMock(spec=file)

        rc = self.md5hasher.check_hash('foo', self.args)
        expected_stdout_calls = [
            call('AUTHORS: FAILED\n'),
            call('README.rst: OK\n'),
            ]
        assert (expected_stdout_calls ==
                self.md5hasher.app.stdout.write.call_args_list)

        expected_stderr_calls = [
            call('hasher md5: WARNING: 1 computed checksum did NOT match\n'),
            ]
        assert (expected_stderr_calls ==
                self.md5hasher.app.stderr.write.call_args_list)
        assert rc == 1

    @patch('__builtin__.open')
    def test_checkresult_display_hasherror_multiple(self, _open):
        _open.side_effect = [
            StringIO(self.check_data),
            StringIO('AUTHORS.\n'),
            StringIO('README.rst.\n'),
            ]
        self.md5hasher.app.stdout = MagicMock(spec=file)
        self.md5hasher.app.stderr = MagicMock(spec=file)

        rc = self.md5hasher.check_hash('foo', self.args)
        expected_stdout_calls = [
            call('AUTHORS: FAILED\n'),
            call('README.rst: FAILED\n'),
            ]
        assert (expected_stdout_calls ==
                self.md5hasher.app.stdout.write.call_args_list)

        expected_stderr_calls = [
            call('hasher md5: WARNING: 2 computed checksums did NOT match\n'),
            ]
        assert (expected_stderr_calls ==
                self.md5hasher.app.stderr.write.call_args_list)
        assert rc == 1

    @patch('__builtin__.open')
    def test_checkresult_display_readerror(self, _open):
        _open.side_effect = [
            StringIO(self.check_data),
            IOError,
            StringIO('README.rst\n'),
            ]
        self.md5hasher.app.stdout = MagicMock(spec=file)
        self.md5hasher.app.stderr = MagicMock(spec=file)

        rc = self.md5hasher.check_hash('foo', self.args)
        expected_stdout_calls = [
            call('AUTHORS: FAILED open or read\n'),
            call('README.rst: OK\n'),
            ]
        assert (expected_stdout_calls ==
                self.md5hasher.app.stdout.write.call_args_list)

        expected_stderr_calls = [
            call('hasher md5: AUTHORS: No such file or directory\n'),
            call('hasher md5: WARNING: 1 listed file could not be read\n'),
            ]
        assert (expected_stderr_calls ==
                self.md5hasher.app.stderr.write.call_args_list)
        assert rc == 1

    @patch('__builtin__.open')
    def test_checkresult_display_readerror_multiple(self, _open):
        _open.side_effect = [
            StringIO(self.check_data),
            IOError,
            IOError,
            ]
        self.md5hasher.app.stdout = MagicMock(spec=file)
        self.md5hasher.app.stderr = MagicMock(spec=file)

        rc = self.md5hasher.check_hash('foo', self.args)
        expected_stdout_calls = [
            call('AUTHORS: FAILED open or read\n'),
            call('README.rst: FAILED open or read\n'),
            ]
        assert (expected_stdout_calls ==
                self.md5hasher.app.stdout.write.call_args_list)

        expected_stderr_calls = [
            call('hasher md5: AUTHORS: No such file or directory\n'),
            call('hasher md5: README.rst: No such file or directory\n'),
            call('hasher md5: WARNING: 2 listed files could not be read\n'),
            ]
        assert (expected_stderr_calls ==
                self.md5hasher.app.stderr.write.call_args_list)
        assert rc == 1

    @patch('__builtin__.open')
    def test_checkresult_quiet(self, _open):
        _open.side_effect = [
            StringIO(self.check_data),
            StringIO('AUTHORS\n'),
            StringIO('README.rst\n'),
            ]
        self.md5hasher.app.stdout = MagicMock(spec=file)
        self.md5hasher.app.stderr = MagicMock(spec=file)

        self.args.quiet = True
        rc = self.md5hasher.check_hash('foo', self.args)
        expected_stdout_calls = []
        assert (expected_stdout_calls ==
                self.md5hasher.app.stdout.write.call_args_list)

        expected_stderr_calls = []
        assert (expected_stderr_calls ==
                self.md5hasher.app.stderr.write.call_args_list)
        assert rc == 0

    @patch('__builtin__.open')
    def test_checkresult_status(self, _open):
        _open.side_effect = [
            StringIO(self.check_data),
            StringIO('AUTHORS\n'),
            StringIO('README.rst\n'),
            ]
        self.md5hasher.app.stdout = MagicMock(spec=file)
        self.md5hasher.app.stderr = MagicMock(spec=file)

        self.args.status = True
        rc = self.md5hasher.check_hash('foo', self.args)
        expected_stdout_calls = []
        assert (expected_stdout_calls ==
                self.md5hasher.app.stdout.write.call_args_list)

        expected_stderr_calls = []
        assert (expected_stderr_calls ==
                self.md5hasher.app.stderr.write.call_args_list)
        assert rc == 0

    @patch('__builtin__.open')
    def test_checkresult_status_hasherror(self, _open):
        _open.side_effect = [
            StringIO(self.check_data),
            StringIO('AUTHORS\n'),
            StringIO('AUTHORS\n'),
            ]
        self.md5hasher.app.stdout = MagicMock(spec=file)
        self.md5hasher.app.stderr = MagicMock(spec=file)

        self.args.status = True
        rc = self.md5hasher.check_hash('foo', self.args)
        expected_stdout_calls = []
        assert (expected_stdout_calls ==
                self.md5hasher.app.stdout.write.call_args_list)

        expected_stderr_calls = []
        assert (expected_stderr_calls ==
                self.md5hasher.app.stderr.write.call_args_list)
        assert rc == 1

    @patch('__builtin__.open')
    def test_checkresult_status_readerror(self, _open):
        _open.side_effect = [
            StringIO(self.check_data),
            StringIO('AUTHORS\n'),
            IOError,
            ]
        self.md5hasher.app.stdout = MagicMock(spec=file)
        self.md5hasher.app.stderr = MagicMock(spec=file)

        self.args.status = True
        rc = self.md5hasher.check_hash('foo', self.args)
        expected_stdout_calls = []
        assert (expected_stdout_calls ==
                self.md5hasher.app.stdout.write.call_args_list)

        expected_stderr_calls = [
            call('hasher md5: README.rst: No such file or directory\n'),
            ]
        assert (expected_stderr_calls ==
                self.md5hasher.app.stderr.write.call_args_list)
        assert rc == 1

    @patch('hasher.hashes.sys')
    def test_checkresult_strict(self, _sys):
        pass

    @patch('__builtin__.open')
    def test_checkresult_warn(self, _open):
        _open.side_effect = [
            StringIO(self.check_data),
            StringIO('AUTHORS\n'),
            StringIO('README.rst\n'),
            ]
        self.md5hasher.app.stdout = MagicMock(spec=file)
        self.md5hasher.app.stderr = MagicMock(spec=file)

        self.args.warn = True
        rc = self.md5hasher.check_hash('foo', self.args)
        expected_stdout_calls = [
            call('AUTHORS: OK\n'),
            call('README.rst: OK\n'),
            ]
        assert (expected_stdout_calls ==
                self.md5hasher.app.stdout.write.call_args_list)
        assert [] == self.md5hasher.app.stderr.write.call_args_list
        assert rc == 0

    @patch('__builtin__.open')
    def test_checkresult_warn_formaterror(self, _open):
        _open.side_effect = [
            StringIO(
                '3ac11b17fa463072f069580031317af2  AUTHORS\n'
                '4e6ee384b7a0a002681cda43a5ccc9d0 +README.rst\n'
                ),
            StringIO('AUTHORS\n'),
            ]
        self.md5hasher.app.stdout = MagicMock(spec=file)
        self.md5hasher.app.stderr = MagicMock(spec=file)

        self.args.warn = True
        rc = self.md5hasher.check_hash('foo', self.args)
        expected_stdout_calls = [
            call('AUTHORS: OK\n'),
            ]
        assert (expected_stdout_calls ==
                self.md5hasher.app.stdout.write.call_args_list)

        expected_stderr_calls = [
            call('hasher md5: foo: 2: improperly formatted MD5 checksum'
                 ' line\n'),
            call('hasher md5: WARNING: 1 line is improperly formatted\n'),
            ]
        assert (expected_stderr_calls ==
                self.md5hasher.app.stderr.write.call_args_list)
        assert rc == 1


if __name__ == '__main__':
    unittest.main()
