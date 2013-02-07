"""
Tests for parser
"""
from ..parser import md5_parser


class TestMd5Parser(object):

    def test_binary_or_text(self):
        """tests binary vs text flags"""
        args = md5_parser.parse_args([])
        assert args.is_text

        args = md5_parser.parse_args(['--binary'])
        assert not args.is_text

        args = md5_parser.parse_args(['--text'])
        assert args.is_text
