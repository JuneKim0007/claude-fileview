"""Replace a file's contents in one step: write <name>.partial beside it, then rename it over the file,
so a reader never sees half a file."""
import os
from pathlib import Path


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(text, encoding="utf-8")
    os.replace(partial, path)
