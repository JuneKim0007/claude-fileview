"""Rules.captures -> captures.json, the stdlib-only form the hook reads. Written atomically, and only
when the content changes, by the supervisor whenever the rules file it tracks changes."""
import json
from pathlib import Path

from fileview.config.atomic_write import atomic_write
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
    atomic_write(path, text)
    return True
