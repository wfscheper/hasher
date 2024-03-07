from __future__ import annotations

from dataclasses import dataclass


@dataclass()
class Args:
    files: list[str]
    check: bool
    binary: bool
    text: bool
    quiet: bool
    status: bool
    warn: bool
    strict: bool
