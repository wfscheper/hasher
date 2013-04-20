'''
Created on Feb 8, 2013

@author: wscheper
'''
import unittest
from StringIO import StringIO

from mock import patch, MagicMock, call

from hasher import (
    FORMAT_ERROR,
    HASH_ERROR,
    READ_ERROR,
    SUCCESS,
    )
from hasher.hashes import base, md5


class TestMD5Hasher(unittest.TestCase):

    def setUp(self):
        self.data = 'a string of data to hash'
        self.data_md5 = '719231ebf10a82f0b9c29c26210a6ec3'
        self.md5hasher = md5.MD5Hasher()

    @patch('hasher.hashes.base.sys')
    def test_basic_hash(self, _sys):
        _sys.stdin = MagicMock()
        _sys.stdin.read.side_effect = [self.data, '']

        expected_result = base.GenerateHashResult('md5sum', '-', self.data_md5)
        result = self.md5hasher.generate_hash('-')
        self.assertEqual(
            expected_result,
            result,
            )

    @patch('__builtin__.open')
    def test_generate_invalid_file(self, _open):
        _open.side_effect = IOError()

        with self.assertRaises(IOError):
            self.md5hasher.generate_hash('md5sum')
        _open.assert_called_once_with('md5sum')

    @patch('hasher.hashes.base.sys')
    def test_generate_display_text(self, _sys):
        _sys.stdout = MagicMock(spec=file)

        base.GenerateHashResult(
            'md5sum',
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
        expected_result = base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', SUCCESS),
            )
        self.assertEqual(expected_result, result)
        self.assertEqual(0, result.format_errors)
        self.assertEqual(0, result.hash_errors)
        self.assertEqual(0, result.read_errors)

    @patch('__builtin__.open')
    def test_check_readerror(self, _open):
        _open.side_effect = [
            StringIO(
                '%s  %s\n' % (self.data_md5, 'bar'),
                ),
            IOError(),
            ]

        result = self.md5hasher.check_hash('foo')
        expected_result = base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', READ_ERROR),
            read_errors=1,
            )

        self.assertEqual(expected_result, result)
        self.assertEqual(0, result.format_errors)
        self.assertEqual(0, result.hash_errors)
        self.assertEqual(1, result.read_errors)

    @patch('__builtin__.open')
    def test_check_mismatch(self, _open):
        _open.side_effect = [
            StringIO('%s  %s\n' % (self.data_md5, 'bar')),
            StringIO(self.data + 'md5sum'),
            ]

        result = self.md5hasher.check_hash('foo')
        expected_result = base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', HASH_ERROR),
            hash_errors=1,
            )
        self.assertEqual(expected_result, result)
        self.assertEqual(0, result.format_errors)
        self.assertEqual(1, result.hash_errors)
        self.assertEqual(0, result.read_errors)

    @patch('__builtin__.open')
    def test_check_formaterror(self, _open):
        _open.side_effect = [
            StringIO('%s +%s\n' % (self.data_md5, 'bar')),
            ]

        result = self.md5hasher.check_hash('foo')
        expected_result = base.CheckHashResult(
            'md5sum',
            'foo',
            (None, FORMAT_ERROR),
            format_errors=1,
            )
        self.assertEqual(expected_result, result)
        self.assertEqual(1, result.format_errors)
        self.assertEqual(0, result.hash_errors)
        self.assertEqual(0, result.read_errors)

    @patch('hasher.hashes.base.sys')
    def test_checkresult_display(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult('md5sum', 'foo', ('bar', SUCCESS)).display()
        self.assertEqual([
            call('bar: OK\n'),
            ],
            _sys.stdout.write.call_args_list,
            )

    @patch('hasher.hashes.base.sys')
    def test_checkresult_display_formaterror(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult('md5sum', 'foo', format_errors=1).display()
        self.assertEqual([], _sys.stdout.write.call_args_list)
        self.assertEqual([
            call('md5sum: WARNING: 1 line is improperly formatted\n'),
            ], _sys.stderr.write.call_args_list)

        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult('md5sum', 'foo', format_errors=2).display()
        self.assertEqual([], _sys.stdout.write.call_args_list)
        self.assertEqual([
            call('md5sum: WARNING: 2 lines are improperly formatted\n'),
            ], _sys.stderr.write.call_args_list)

    @patch('hasher.hashes.base.sys')
    def test_checkresult_display_hasherror(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', HASH_ERROR),
            hash_errors=1,
            ).display()
        self.assertEqual([
            call('bar: FAILED\n'),
            ],
            _sys.stdout.write.call_args_list,
            )
        self.assertEqual([
            call('md5sum: WARNING: 1 computed checksum did NOT match\n'),
            ],
            _sys.stderr.write.call_args_list,
            )

        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', HASH_ERROR),
            ('baz', HASH_ERROR),
            hash_errors=2,
            ).display()
        self.assertEqual([
            call('bar: FAILED\n'),
            call('baz: FAILED\n'),
            ],
            _sys.stdout.write.call_args_list,
            )
        self.assertEqual([
            call('md5sum: WARNING: 2 computed checksums did NOT match\n'),
            ],
            _sys.stderr.write.call_args_list,
            )

    @patch('hasher.hashes.base.sys')
    def test_checkresult_display_readerror(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', READ_ERROR),
            read_errors=1,
            ).display()
        self.assertEqual([
            call('bar: FAILED open or read\n'),
            ],
            _sys.stdout.write.call_args_list,
            )
        self.assertEqual([
            call('md5sum: bar: No such file or directory\n'),
            call('md5sum: WARNING: 1 listed file could not be read\n'),
            ],
            _sys.stderr.write.call_args_list,
            )

        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', READ_ERROR),
            ('baz', READ_ERROR),
            read_errors=2,
            ).display()
        self.assertEqual([
            call('bar: FAILED open or read\n'),
            call('baz: FAILED open or read\n'),
            ],
            _sys.stdout.write.call_args_list,
            )
        self.assertEqual([
            call('md5sum: bar: No such file or directory\n'),
            call('md5sum: baz: No such file or directory\n'),
            call('md5sum: WARNING: 2 listed files could not be read\n'),
            ],
            _sys.stderr.write.call_args_list,
            )

    @patch('hasher.hashes.base.sys')
    def test_checkresult_status(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', SUCCESS),
            ).display(status=True)
        self.assertEqual([], _sys.stdout.write.call_args_list)
        self.assertEqual([], _sys.stderr.write.call_args_list)

    @patch('hasher.hashes.base.sys')
    def test_checkresult_status_hasherror(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', SUCCESS),
            hash_errors=1,
            ).display(status=True)
        self.assertEqual([], _sys.stdout.write.call_args_list)
        self.assertEqual([], _sys.stderr.write.call_args_list)

    @patch('hasher.hashes.base.sys')
    def test_checkresult_status_readerror(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', READ_ERROR),
            read_errors=1,
            ).display(status=True)
        self.assertEqual([], _sys.stdout.write.call_args_list)
        self.assertEqual([
            call('md5sum: bar: No such file or directory\n'),
            ],
            _sys.stderr.write.call_args_list,
            )

    @patch('hasher.hashes.base.sys')
    def test_checkresult_strict(self, _sys):
        pass

    @patch('hasher.hashes.base.sys')
    def test_checkresult_warn(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', SUCCESS),
            ).display(warn=True)
        self.assertEqual([
            call('bar: OK\n'),
            ],
            _sys.stdout.write.call_args_list,
            )
        self.assertEqual([], _sys.stderr.write.call_args_list)

    @patch('hasher.hashes.base.sys')
    def test_checkresult_warn_formaterror(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', SUCCESS),
            (None, FORMAT_ERROR),
            format_errors=1,
            ).display(warn=True)
        self.assertEqual([
            call('bar: OK\n'),
            ],
            _sys.stdout.write.call_args_list,
            )
        self.assertEqual([
            call('md5sum: foo: 2: improperly formatted checksum line\n'),
            call('md5sum: WARNING: 1 line is improperly formatted\n'),
            ],
            _sys.stderr.write.call_args_list,
            )

    @patch('hasher.hashes.base.sys')
    def test_checkresult_quiet(self, _sys):
        _sys.stdout = MagicMock(spec=file)
        _sys.stderr = MagicMock(spec=file)

        base.CheckHashResult(
            'md5sum',
            'foo',
            ('bar', SUCCESS),
            ).display(quiet=True)
        self.assertEqual([], _sys.stdout.write.call_args_list)
        self.assertEqual([], _sys.stdout.write.call_args_list)
