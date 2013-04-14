'''
Created on Feb 8, 2013

@author: wscheper
'''
import unittest

from mock import patch, MagicMock

from hasher.hashes import md5
from StringIO import StringIO


class TestMD5Hasher(unittest.TestCase):

    def setUp(self):
        self.data = 'a string of data to hash'
        self.data_md5 = '719231ebf10a82f0b9c29c26210a6ec3'
        self.md5hasher = md5.MD5Hasher()

    @patch('hasher.hashes.base.sys')
    def test_basic_hash(self, _sys):
        _sys.stdin = MagicMock()
        _sys.stdin.read.side_effect = [self.data, '']

        expected_result = ('-', self.data_md5,)
        result = self.md5hasher.generate_hash('-')
        self.assertEqual(
            expected_result,
            result,
            'Expected %s, but got %s' % (expected_result, result),
            )

    @patch('__builtin__.open')
    def test_generate_invalid_file(self, _open):
        _open.side_effect = IOError()

        with self.assertRaises(IOError):
            self.md5hasher.generate_hash('foo')
        _open.assert_called_once_with('foo')

    @patch('__builtin__.open')
    def test_check_data(self, _open):
        _open.side_effect = [
            StringIO(
                '%s  %s\n' % (self.data_md5, 'foo'),
                ),
            StringIO(
                self.data,
                ),
            ]

        expected_result = (
            [('foo', 'OK',)],
            (0, 0, 0),
            )

        self.assertEqual(expected_result, self.md5hasher.check_hash('foo'))

    @patch('__builtin__.open')
    def test_check_readerror(self, _open):
        _open.side_effect = [
            StringIO(
                '%s  %s\n' % (self.data_md5, 'foo'),
                ),
            IOError(),
            ]

        expected_result = (
            [('foo', 'FAILED open or read',), ],
            (0, 0, 1),
            )
        self.assertEqual(expected_result, self.md5hasher.check_hash('foo'))

    @patch('__builtin__.open')
    def test_check_mismatch(self, _open):
        _open.side_effect = [
            StringIO('%s  %s\n' % (self.data_md5, 'foo')),
            StringIO(self.data + ' foo'),
            ]

        expected_result = (
            [('foo', 'FAILED',), ],
            (0, 1, 0),
            )
        self.assertEqual(expected_result, self.md5hasher.check_hash('foo'))

    @patch('__builtin__.open')
    def test_check_formaterror(self, _open):
        _open.side_effect = [
            StringIO('%s +%s\n' % (self.data_md5, 'foo')),
            ]

        expected_result = (
            [],
            (1, 0, 0),
            )
        self.assertEqual(expected_result, self.md5hasher.check_hash('foo'))
