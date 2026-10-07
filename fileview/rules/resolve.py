"""Apply rules to one absolute path: where it lives (label + rest), whether it is shown, how it is
coloured. visible = not ignored, or deignored. Colour is decided independently of visibility."""
import fnmatch
import os
import re
from dataclasses import dataclass
from functools import lru_cache

from fileview.rules.model import Colour, PatternSet, Rules


@dataclass(frozen=True)
class PathView:
    label: str            # "" inside the project root, else a prefix label or ""
    label_colour: Colour  # "" means the palette's label colour
    rest: str             # path after the root / prefix, or ~-abbreviated absolute path
    colour: Colour        # "" means the default colour
    visible: bool


def resolve(path: str, root: str, rules: Rules) -> PathView:
    label, label_colour, rest = _locate(path, root, rules)
    visible = not _matches_any(path, rules.ignore) or _matches_any(path, rules.deignore)
    colour = next((r.colour for r in rules.colour if _matches(path, r.glob, r.regex)), "")
    return PathView(label, label_colour, rest, colour, visible)


def _locate(path: str, root: str, rules: Rules) -> tuple[str, Colour, str]:
    if root and _under(path, root):
        return "", "", os.path.relpath(path, root)
    best = None
    for prefix in rules.prefixes:
        directory = _expand(prefix.path)
        if _under(path, directory) and (best is None or len(directory) > len(best[0])):
            best = (directory, prefix)
    if best:
        directory, prefix = best
        return prefix.label, prefix.colour, os.path.relpath(path, directory) if path != directory else "."
    home = os.path.expanduser("~")
    return "", "", "~" + path[len(home):] if _under(path, home) else path


def _matches_any(path: str, patterns: PatternSet) -> bool:
    return any(_matches(path, glob, "") for glob in patterns.glob) or \
        any(_matches(path, "", regex) for regex in patterns.regex)


def _matches(path: str, glob: str, regex: str) -> bool:
    if glob:
        return fnmatch.fnmatch(path, _expand_glob(glob))
    return bool(regex) and _compiled(regex).search(path) is not None


@lru_cache(maxsize=256)
def _compiled(pattern: str) -> re.Pattern:
    return re.compile(pattern)


@lru_cache(maxsize=256)
def _expand_glob(glob: str) -> str:
    return os.path.expanduser(glob) if glob.startswith("~") else glob


@lru_cache(maxsize=64)
def _expand(directory: str) -> str:
    return os.path.normpath(os.path.expanduser(directory))


def _under(path: str, directory: str) -> bool:
    return path == directory or path.startswith(directory.rstrip(os.sep) + os.sep)
