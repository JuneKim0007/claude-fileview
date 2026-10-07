"""The capture patterns the hook applies, read from captures.json (written by the supervisor from the
rules file). Standard library only, so the hook never imports yaml. Anything wrong with the file
means "capture nothing"; the hook must never fail because of it."""
import json
import re
from dataclasses import dataclass
from pathlib import Path

from fileview.locations import CAPTURES_FILE

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class CompiledCapture:
    name: str
    command: re.Pattern
    output: re.Pattern | None


def load(path: Path = CAPTURES_FILE) -> list[CompiledCapture]:
    try:
        document = json.loads(path.read_text())
        if document.get("schemaVersion") != SCHEMA_VERSION:
            return []
        return [CompiledCapture(item["name"], re.compile(item["command"]),
                                re.compile(item["output"]) if item.get("output") else None)
                for item in document["captures"]]
    except (OSError, ValueError, KeyError, TypeError, re.error):
        return []
