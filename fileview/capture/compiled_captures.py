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
    except (OSError, ValueError):
        return []
    items = _capture_items(document)
    if items is None:
        return []
    try:
        return [CompiledCapture(item["name"], re.compile(item["command"]),
                                re.compile(item["output"]) if item.get("output") else None)
                for item in items]
    except re.error:
        return []


def _capture_items(document: object) -> list[dict] | None:
    """The capture entries when the whole document has the exported shape, else None: one bad entry
    disables every capture, so the hook never runs half a rule set."""
    if not isinstance(document, dict) or document.get("schemaVersion") != SCHEMA_VERSION:
        return None
    items = document.get("captures")
    if not isinstance(items, list) or not all(_is_capture(item) for item in items):
        return None
    return items


def _is_capture(item: object) -> bool:
    return (isinstance(item, dict)
            and isinstance(item.get("name"), str)
            and isinstance(item.get("command"), str)
            and (item.get("output") is None or isinstance(item.get("output"), str)))
