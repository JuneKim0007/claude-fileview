"""Validators every section uses: a colour must resolve, a regex must compile. Each failure is a
ConfigError naming the dotted path."""
import re

from fileview.config.errors import ConfigError
from fileview.rules.colours import sgr


def colour(value, custom: dict, path: str):
    try:
        sgr(value, custom)
    except ValueError as failure:
        raise ConfigError("unknown_colour", path=path, detail=str(failure)) from failure
    return value


def regex(pattern: str, path: str) -> str:
    try:
        re.compile(pattern)
    except re.error as failure:
        raise ConfigError("bad_regex", path=path, detail=f"{pattern!r}: {failure}") from failure
    return pattern
