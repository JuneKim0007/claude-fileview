"""Rules.captures -> captures.json, the stdlib-only form the hook reads. Written atomically, and only
when the content changes, by the supervisor whenever the rules file it tracks changes."""
import json
import os
from pathlib import Path

from fileview.locations import CAPTURES_FILE
from fileview.rules.model import CaptureRule

SCHEMA_VERSION = 1


def export(captures: tuple[CaptureRule, ...], path: Path = CAPTURES_FILE) -> bool:
    """True when the file was (re)written."""
    document = {"schemaVersion": SCHEMA_VERSION,
                "captures": [{"name": c.name, "command": c.command, "output": c.output} for c in captures]}
    text = json.dumps(document, indent=1)
    try:
        if path.read_text() == text:
            return False
    except OSError:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(text)
    os.replace(partial, path)
    return True
