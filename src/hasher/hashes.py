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

from io import open
from typing import IO, TYPE_CHECKING, Any, Callable, ClassVar, Iterator, Pattern, cast
import hashlib
import logging
import os
import re
import sys

if TYPE_CHECKING:
    Hash = hashlib._Hash
else:
    Hash = None

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol


FORMAT_ERROR = "MISFORMATTED"
HASH_ERROR = "FAILED"
READ_ERROR = "FAILED open or read"
SUCCESS = "OK"
EXCLUDES = ("base.py", "__init__.py")
PATH = os.path.dirname(__file__)
PYEXT = ".py"
STATUS_MSG = "{0}: {1}"


class Writer(Protocol):
    def __call__(self, message: Any, *args: Any, **kwargs: Any) -> None:
        ...


class Hasher:
    """
    Base class for various sub-classes that implement specific hashing
    algorithms.
    """

    CHECK_RE: ClassVar[Pattern]
    hashlib: ClassVar[Callable[..., Hash]]
    name: ClassVar[str]

    log = logging.getLogger(__name__)

    def __init__(self, stdout: Writer, stderr: Writer) -> None:
        self.chunk_size = 64 * 2048
        self.stdout = stdout
        self.stderr = stderr

    def _calculate_hash(self, file_object: IO) -> str:
        """
        Calculate a hash value for the data in ``file_object
        """
        hasher = self.hashlib()
        for chunk in self.iterchunks(file_object):
            hasher.update(chunk)
        return hasher.hexdigest()

    def _open_file(self, fname: str, binary: bool = False) -> IO:
        if fname == "-":
            return sys.stdin
        return open(fname, "rb" if binary else "r")

    def check_hash(self, fname: str, args: Any) -> int:
        """
        Check the hashed values in files against the calculated values

        Returns a list and a tuple of error counts.

        list: [(fname, 'OK' or 'FAILED' or 'FAILED open or read'),...]
        Error counts: (format_erros, hash_errors, read_errors)
        """
        fobj = self._open_file(fname, args.binary)

        rc = 0
        format_errors = 0
        hash_errors = 0
        read_errors = 0
        for idx, line in enumerate(fobj):
            # remove any newline characters
            m = self.CHECK_RE.match(line.strip())
            if not m:
                if args.warn:
                    self.stderr(
                        f"hasher {self.name}: {fname}: {idx+1}: improperly formatted "
                        f"{self.name.upper()} checksum line"
                    )
                format_errors += 1
                rc = 1
                continue
            hash_value, binary, check_file = m.groups()

            try:
                check_f = open(check_file, "rb" if binary == "*" else "r")
            except IOError:
                self.stderr(
                    f"hasher {self.name}: {check_file}: No such file or directory"
                )
                if not args.status:
                    self.stdout(STATUS_MSG.format(check_file, READ_ERROR))
                read_errors += 1
                rc = 1
                continue

            if self._calculate_hash(check_f) == hash_value:
                if not (args.quiet or args.status):
                    self.stdout(STATUS_MSG.format(check_file, SUCCESS))
            else:
                if not args.status:
                    self.stdout(STATUS_MSG.format(check_file, HASH_ERROR))
                hash_errors += 1
                rc = 1

        if format_errors and not args.status:
            lines = "line" + ("s" if format_errors > 1 else "")
            are = "are" if format_errors > 1 else "is"
            self.stderr(
                f"hasher {self.name}: WARNING: {format_errors} {lines} {are} "
                "improperly formatted"
            )
        if read_errors and not args.status:
            files = "file" + ("s" if read_errors > 1 else "")
            self.stderr(
                f"hasher {self.name}: WARNING: {read_errors} listed {files} "
                "could not be read"
            )
        if hash_errors and not args.status:
            checksums = "checksum" + ("s" if hash_errors > 1 else "")
            self.stderr(
                f"hasher {self.name}: WARNING: {hash_errors} computed {checksums} "
                "did NOT match"
            )
        return rc

    def generate_hash(self, fname: str, args: Any) -> None:
        """Generate hashes for files"""
        fobj = self._open_file(fname, args.binary)
        hash_value = self._calculate_hash(fobj)

        line = f"{hash_value} {'*' if args.binary else ' '}{fname}"

        if "//" in line:
            line = "//" + line.replace("//", "////")
        self.stdout(line)

    def iterchunks(self, file_object: IO) -> Iterator[bytes]:
        data = file_object.read(self.chunk_size)
        if isinstance(data, str):
            while data != "":
                yield cast(str, data).encode("utf-8")
                data = file_object.read(self.chunk_size)
        else:
            while data != b"":
                yield cast(bytes, data)
                data = file_object.read(self.chunk_size)

    def take_action(self, parsed_args: Any) -> None:
        if parsed_args.check and (parsed_args.binary and parsed_args.text):
            raise RuntimeError(
                "the --binary and --text options are meaningless when "
                "verifying checksums"
            )

        if not parsed_args.check and (
            parsed_args.warn
            or parsed_args.status
            or parsed_args.quiet
            or parsed_args.strict
        ):
            raise RuntimeError(
                "the --warn, --status, and --quiet options are meaningful "
                "only when verifying checksums"
            )

        if not parsed_args.files:
            parsed_args.files = ["-"]

        for fname in parsed_args.files:
            if parsed_args.check:
                self.check_hash(fname, parsed_args)
            else:
                self.generate_hash(fname, parsed_args)


class MD5Hasher(Hasher):
    CHECK_RE = re.compile(r"^([a-f0-9]{32}) (\*| )(.+)$")
    name = "md5"
    hashlib = hashlib.md5


class SHA1Hasher(Hasher):
    CHECK_RE = re.compile(r"^([a-f0-9]{40}) (\*| )(.+)$")
    name = "sha1"
    hashlib = hashlib.sha1


class SHA256Hasher(Hasher):
    CHECK_RE = re.compile(r"^([a-f0-9]{64}) (\*| )(.+)$")
    name = "sha256"
    hashlib = hashlib.sha256
