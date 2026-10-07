"""Where a path lives, as shown (layer 6 of the pipeline): relative to the project root, or a prefix
label plus the rest, or ~-abbreviated. Longest prefix wins; the project root beats every prefix."""
import os
from dataclasses import dataclass
from functools import lru_cache

from fileview.rules.model import Colour, Rules


@dataclass(frozen=True)
class Placement:
    label: str            # "" inside the project root, else a prefix label or ""
    label_colour: Colour  # "" means the palette's label colour
    rest: str             # path after the root / prefix, or ~-abbreviated absolute path

    def text(self) -> str:
        return f"[{self.label}] {self.rest}" if self.label else self.rest


def place(path: str, root: str, rules: Rules) -> Placement:
    if root and _under(path, root):
        return Placement("", "", os.path.relpath(path, root))
    best = None
    for prefix in rules.prefixes:
        directory = _expand(prefix.path)
        if _under(path, directory) and (best is None or len(directory) > len(best[0])):
            best = (directory, prefix)
    if best:
        directory, prefix = best
        return Placement(prefix.label, prefix.colour, os.path.relpath(path, directory) if path != directory else ".")
    home = os.path.expanduser("~")
    return Placement("", "", "~" + path[len(home):] if _under(path, home) else path)


@lru_cache(maxsize=64)
def _expand(directory: str) -> str:
    return os.path.normpath(os.path.expanduser(directory))


def _under(path: str, directory: str) -> bool:
    return path == directory or path.startswith(directory.rstrip(os.sep) + os.sep)
