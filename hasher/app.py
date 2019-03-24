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

import functools
import logging

import click

from .hashes import MD5Hasher

log = logging.getLogger(__name__)


class AttrDict:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@click.group()
@click.version_option()
@click.option("-v", "--verbose", count=True, default=0, help="Increase verbosity of output. Can be repeated.")
@click.option(
    "--log-file",
    default=None,
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
    help="Specify a file to log output. Disabled by default.",
)
@click.option("--debug/--no-debug", default=False, help="Show tracebacks on errors")
@click.pass_context
def hasher(ctx, verbose, log_file, debug):
    ctx.ensure_object(dict)
    log.debug("setting debug mode to '%s'", str(debug))
    ctx.obj["DEBUG"] = debug
    if verbose == 0:
        log_level = logging.WARN
    elif verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    log_config = dict(level=log_level)
    if log_file is not None:
        log_config["filename"] = log_file
    logging.basicConfig(**log_config)


hasher_options = [
    (("-c", "--check"), dict(is_flag=True, help="read hashes from FILEs and check them")),
    (("-b", "--binary", "mode"), dict(flag_value="binary", help="read in binary mode")),
    (("-t", "--text", "mode"), dict(flag_value="text", default=True, help="read in text mode (default)")),
    (("--quiet",), dict(is_flag=True, help="don't print OK for each successfully verified file")),
    (("--status",), dict(is_flag=True, help="don't output anything, status code shows success")),
    (("-w", "--warn"), dict(is_flag=True, help="warn about improperly formatted checksum lines")),
    (("--strict",), dict(is_flag=True, help="with --check, exit non-zero for any invalid input")),
]

hasher_arguments = [(("files",), dict(nargs=-1, type=click.Path(exists=True, dir_okay=False, resolve_path=True, allow_dash=True)))]


@click.pass_context
def md5(ctx, files, check, mode, quiet, status, warn, strict):
    _hasher(MD5Hasher, files, check, mode, quiet, status, warn, strict)


def _hasher(klass, files, check, mode, quiet, status, warn, strict):
    args = AttrDict(
        files=files,
        check=check,
        binary=(mode == "binary"),
        text=(mode == "text"),
        quiet=quiet,
        status=status,
        warn=warn,
        strict=strict,
    )
    hasher = klass(click.echo, functools.partial(click.echo, error=True))
    hasher.take_action(args)


for args, kwargs in hasher_arguments:
    md5 = click.argument(*args, **kwargs)(md5)

for args, kwargs in hasher_options:
    md5 = click.option(*args, **kwargs)(md5)
md5 = hasher.command()(md5)
