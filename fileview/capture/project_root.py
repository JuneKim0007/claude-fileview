"""cwd -> the enclosing git work tree, found by walking up; no subprocess, so it stays fast in a hook."""
import os
from functools import lru_cache


@lru_cache(maxsize=32)
def project_root(cwd: str) -> str:
    current = os.path.abspath(cwd) if cwd else ""
    while current and current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, ".git")):
            return current
        current = os.path.dirname(current)
    return os.path.abspath(cwd) if cwd else ""
