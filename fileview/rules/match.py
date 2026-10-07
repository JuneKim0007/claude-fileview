"""The one matcher every rule layer uses, so ignore, colour, announce and display select events the
same way. Patterns are compiled once and cached."""
import fnmatch
import os
import re
from functools import lru_cache

from fileview.rules.model import Match, PatternSet


def matches(match: Match, kind: str, command: str, path: str) -> bool:
    if match.kinds and kind not in match.kinds:
        return False
    if match.command and not (command and compiled(match.command).search(command)):
        return False
    if (match.glob or match.regex) and not (path and path_matches(path, match.glob, match.regex)):
        return False
    return True


def in_set(patterns: PatternSet, kind: str, command: str, path: str) -> bool:
    if path and any(path_matches(path, glob, "") for glob in patterns.glob):
        return True
    if path and any(path_matches(path, "", regex) for regex in patterns.regex):
        return True
    return any(matches(m, kind, command, path) for m in patterns.match)


def path_matches(path: str, glob: str, regex: str) -> bool:
    if glob and not fnmatch.fnmatch(path, _expand(glob)):
        return False
    if regex and not compiled(regex).search(path):
        return False
    return bool(glob or regex)


@lru_cache(maxsize=512)
def compiled(pattern: str) -> re.Pattern:
    return re.compile(pattern)


@lru_cache(maxsize=256)
def _expand(glob: str) -> str:
    return os.path.expanduser(glob) if glob.startswith("~") else glob
