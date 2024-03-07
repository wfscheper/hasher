from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from hasher.app import hasher
import pytest


def test_hasher_usage():
    runner = CliRunner()
    result = runner.invoke(
        hasher,
    )
    assert result.exit_code == 0
    assert (
        """Usage: hasher [OPTIONS] COMMAND [ARGS]...

Options:
  --version             Show the version and exit.
  -v, --verbose         Increase verbosity of output. Can be repeated.
  --log-file FILE       Specify a file to log output. Disabled by default.
  --debug / --no-debug  Show tracebacks on errors
  --help                Show this message and exit.

Commands:
  md5     Generate or check md5 hashes
  sha1    Generate or check sha1 hashes
  sha256  Generate or check sha256 hashes
"""
        == result.output
    )


def test_hasher_missing_command():
    runner = CliRunner()
    result = runner.invoke(hasher, ["-v"])
    assert 2 == result.exit_code
    assert (
        """Usage: hasher [OPTIONS] COMMAND [ARGS]...
Try 'hasher --help' for help.

Error: Missing command.
"""
        == result.output
    )


test_inputs = [
    ("md5", "d8e8fca2dc0f896fd7cb4cb0031ba249"),
    ("sha1", "4e1243bd22c66e76c2ba9eddc1f91394e57f9f83"),
    ("sha256", "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2"),
]


@pytest.mark.parametrize("hash,expected", test_inputs)
def test_stdin(hash: str, expected: str):
    runner = CliRunner()
    result = runner.invoke(hasher, [hash], input="test\n")
    assert 0 == result.exit_code
    assert f"{expected}  -\n" == result.output


@pytest.mark.parametrize("hash,expected", test_inputs)
def test_file(hash: str, expected: str):
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("test.txt").write_text("test\n")
        result = runner.invoke(hasher, [hash, "test.txt"])
        assert 0 == result.exit_code, result.output
        assert f"{expected}  test.txt\n" == result.output


@pytest.mark.parametrize("hash,checksum", test_inputs)
def test_check(hash: str, checksum: str):
    runner = CliRunner(mix_stderr=False)
    with runner.isolated_filesystem():
        Path("test1.txt").write_text("test\n")
        Path("test2.txt").write_text("test\n")
        Path("checksums.txt").write_text(
            f"{checksum}  test1.txt\n{checksum.replace('2', '3')}  test2.txt\n"
        )
        result = runner.invoke(hasher, [hash, "--check", "checksums.txt"])
        assert 0 == result.exit_code, result.output
        assert "test1.txt: OK\ntest2.txt: FAILED\n" == result.output
        assert (
            f"hasher {hash}: WARNING: 1 computed checksum did NOT match\n"
            == result.stderr
        )


@pytest.mark.parametrize("hash,checksum", test_inputs)
def test_check_bad_format(hash: str, checksum: str):
    runner = CliRunner(mix_stderr=False)
    with runner.isolated_filesystem():
        Path("test1.txt").write_text("test\n")
        Path("checksums.txt").write_text(f"{checksum} test1.txt\n")
        result = runner.invoke(hasher, [hash, "--check", "checksums.txt"])
        assert 0 == result.exit_code, result.output
        assert "" == result.output
        assert (
            f"hasher {hash}: WARNING: 1 line is improperly formatted\n" == result.stderr
        )


@pytest.mark.parametrize("hash,checksum", test_inputs)
def test_check_bad_format_strict(hash: str, checksum: str):
    runner = CliRunner(mix_stderr=False)
    with runner.isolated_filesystem():
        Path("test1.txt").write_text("test\n")
        Path("checksums.txt").write_text(f"{checksum} test1.txt\n")
        result = runner.invoke(hasher, [hash, "--check", "--strict", "checksums.txt"])
        assert 0 == result.exit_code, result.output
        assert "" == result.output
        assert (
            f"hasher {hash}: WARNING: 1 line is improperly formatted\n" == result.stderr
        )


@pytest.mark.parametrize("hash,checksum", test_inputs)
def test_check_strict(hash: str, checksum: str):
    runner = CliRunner(mix_stderr=False)
    with runner.isolated_filesystem():
        Path("test1.txt").write_text("test\n")
        Path("test2.txt").write_text("test\n")
        Path("checksums.txt").write_text(
            f"{checksum}  test1.txt\n{checksum.replace('2', '3')}  test2.txt\n"
        )
        result = runner.invoke(hasher, [hash, "--check", "--strict", "checksums.txt"])
        assert 0 == result.exit_code, result.output
        assert "test1.txt: OK\ntest2.txt: FAILED\n" == result.output
        assert (
            f"hasher {hash}: WARNING: 1 computed checksum did NOT match\n"
            == result.stderr
        )
