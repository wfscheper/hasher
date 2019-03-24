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
import io

import pytest


@pytest.fixture
def md5hasher(mocker):
    from hasher import hashes

    md5hasher = hashes.MD5Hasher(mocker.MagicMock(name="stdout"), mocker.MagicMock(name="stderr"))
    return md5hasher


@pytest.fixture
def args():
    from hasher.app import AttrDict

    return AttrDict(binary=False, warn=False, status=False, quiet=False)


class TestMD5Hasher:
    data = u"a string of data to hash\n"
    data_md5 = hashlib.md5(data.encode("utf-8")).hexdigest()
    check_data = u"3ac11b17fa463072f069580031317af2  AUTHORS\n4e6ee384b7a0a002681cda43a5ccc9d0  README.rst\n"

    def test_generate_invalid_file(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = IOError()

        with pytest.raises(IOError):
            md5hasher.generate_hash("foo", args)
        _open.assert_called_once_with("foo", "r")

    def test_generate_display_text(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open(read_data=self.data))

        md5hasher.generate_hash("foo", args)

        _open.assert_called_once_with("foo", "r")
        md5hasher.stdout.assert_called_with("%s  foo\n" % self.data_md5)

    def test_generate_display_text_binary(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open(read_data=self.data.encode("utf-8")))
        args.binary = True

        md5hasher.generate_hash("foo", args)

        _open.assert_called_once_with("foo", "rb")
        md5hasher.stdout.assert_called_with("%s *foo\n" % self.data_md5)

    def test_checkresult_display(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = [io.StringIO(self.check_data), io.StringIO(u"AUTHORS\n"), io.StringIO(u"README.rst\n")]

        rc = md5hasher.check_hash("foo", args)

        expected_stdout_calls = [mocker.call("AUTHORS: OK\n"), mocker.call("README.rst: OK\n")]
        assert expected_stdout_calls == md5hasher.stdout.call_args_list
        assert rc == 0

    def test_checkresult_display_formaterror(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = [
            io.StringIO(
                u"1234  File\n"
                u"1111111111111111111111111111111  File2\n"
                u"f2cd884501b6913cad2ae243475a75d3 +README.rst\n"
                u"111111111111111111111111111111111  File2\n"
                u"1111111111111111111111111111111111  File2\n"
            )
        ]

        rc = md5hasher.check_hash("foo", args)

        assert [] == md5hasher.stdout.call_args_list

        expected_stderr_calls = [mocker.call("hasher md5: WARNING: 5 lines are improperly formatted\n")]
        assert expected_stderr_calls == md5hasher.stderr.call_args_list
        assert rc == 1

    def test_checkresult_display_hasherror(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = [io.StringIO(self.check_data), io.StringIO(u"AUTHORS.\n"), io.StringIO(u"README.rst\n")]

        rc = md5hasher.check_hash("foo", args)
        expected_stdout_calls = [mocker.call("AUTHORS: FAILED\n"), mocker.call("README.rst: OK\n")]
        assert expected_stdout_calls == md5hasher.stdout.call_args_list

        expected_stderr_calls = [mocker.call("hasher md5: WARNING: 1 computed checksum did NOT match\n")]
        assert expected_stderr_calls == md5hasher.stderr.call_args_list
        assert rc == 1

    def test_checkresult_display_hasherror_multiple(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = [io.StringIO(self.check_data), io.StringIO(u"AUTHORS.\n"), io.StringIO(u"README.rst.\n")]

        rc = md5hasher.check_hash("foo", args)
        expected_stdout_calls = [mocker.call("AUTHORS: FAILED\n"), mocker.call("README.rst: FAILED\n")]
        assert expected_stdout_calls == md5hasher.stdout.call_args_list

        expected_stderr_calls = [mocker.call("hasher md5: WARNING: 2 computed checksums did NOT match\n")]
        assert expected_stderr_calls == md5hasher.stderr.call_args_list
        assert rc == 1

    def test_checkresult_display_readerror(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = [io.StringIO(self.check_data), IOError, io.StringIO(u"README.rst\n")]

        rc = md5hasher.check_hash("foo", args)

        expected_stdout_calls = [mocker.call("AUTHORS: FAILED open or read\n"), mocker.call("README.rst: OK\n")]
        assert expected_stdout_calls == md5hasher.stdout.call_args_list

        expected_stderr_calls = [
            mocker.call("hasher md5: AUTHORS: No such file or directory\n"),
            mocker.call("hasher md5: WARNING: 1 listed file could not be read\n"),
        ]
        assert expected_stderr_calls == md5hasher.stderr.call_args_list
        assert rc == 1

    def test_checkresult_display_readerror_multiple(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = [io.StringIO(self.check_data), IOError, IOError]

        rc = md5hasher.check_hash("foo", args)
        expected_stdout_calls = [mocker.call("AUTHORS: FAILED open or read\n"), mocker.call("README.rst: FAILED open or read\n")]
        assert expected_stdout_calls == md5hasher.stdout.call_args_list

        expected_stderr_calls = [
            mocker.call("hasher md5: AUTHORS: No such file or directory\n"),
            mocker.call("hasher md5: README.rst: No such file or directory\n"),
            mocker.call("hasher md5: WARNING: 2 listed files could not be read\n"),
        ]
        assert expected_stderr_calls == md5hasher.stderr.call_args_list
        assert rc == 1

    def test_checkresult_quiet(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = [io.StringIO(self.check_data), io.StringIO(u"AUTHORS\n"), io.StringIO(u"README.rst\n")]

        args.quiet = True
        rc = md5hasher.check_hash("foo", args)
        expected_stdout_calls = []
        assert expected_stdout_calls == md5hasher.stdout.call_args_list

        expected_stderr_calls = []
        assert expected_stderr_calls == md5hasher.stderr.call_args_list
        assert rc == 0

    def test_checkresult_status(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = [io.StringIO(self.check_data), io.StringIO(u"AUTHORS\n"), io.StringIO(u"README.rst\n")]

        args.status = True
        rc = md5hasher.check_hash("foo", args)
        expected_stdout_calls = []
        assert expected_stdout_calls == md5hasher.stdout.call_args_list

        expected_stderr_calls = []
        assert expected_stderr_calls == md5hasher.stderr.call_args_list
        assert rc == 0

    def test_checkresult_status_hasherror(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = [io.StringIO(self.check_data), io.StringIO(u"AUTHORS\n"), io.StringIO(u"AUTHORS\n")]

        args.status = True
        rc = md5hasher.check_hash("foo", args)
        expected_stdout_calls = []
        assert expected_stdout_calls == md5hasher.stdout.call_args_list

        expected_stderr_calls = []
        assert expected_stderr_calls == md5hasher.stderr.call_args_list
        assert rc == 1

    def test_checkresult_status_readerror(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = [io.StringIO(self.check_data), io.StringIO(u"AUTHORS\n"), IOError]

        args.status = True
        rc = md5hasher.check_hash("foo", args)
        expected_stdout_calls = []
        assert expected_stdout_calls == md5hasher.stdout.call_args_list

        expected_stderr_calls = [mocker.call("hasher md5: README.rst: No such file or directory\n")]
        assert expected_stderr_calls == md5hasher.stderr.call_args_list
        assert rc == 1

    def test_checkresult_warn(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = [io.StringIO(self.check_data), io.StringIO(u"AUTHORS\n"), io.StringIO(u"README.rst\n")]

        args.warn = True
        rc = md5hasher.check_hash("foo", args)
        expected_stdout_calls = [mocker.call("AUTHORS: OK\n"), mocker.call("README.rst: OK\n")]
        assert expected_stdout_calls == md5hasher.stdout.call_args_list
        assert [] == md5hasher.stderr.call_args_list
        assert rc == 0

    def test_checkresult_warn_formaterror(self, mocker, md5hasher, args):
        _open = mocker.patch("hasher.hashes.open", mocker.mock_open())
        _open.side_effect = [
            io.StringIO(u"3ac11b17fa463072f069580031317af2  AUTHORS\n4e6ee384b7a0a002681cda43a5ccc9d0 +README.rst\n"),
            io.StringIO(u"AUTHORS\n"),
        ]

        args.warn = True
        rc = md5hasher.check_hash("foo", args)
        expected_stdout_calls = [mocker.call("AUTHORS: OK\n")]
        assert expected_stdout_calls == md5hasher.stdout.call_args_list

        expected_stderr_calls = [
            mocker.call("hasher md5: foo: 2: improperly formatted MD5 checksum" " line\n"),
            mocker.call("hasher md5: WARNING: 1 line is improperly formatted\n"),
        ]
        assert expected_stderr_calls == md5hasher.stderr.call_args_list
        assert rc == 1
