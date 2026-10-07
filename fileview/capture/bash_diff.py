"""CREATE / WRITE / DELETE events from the harness's diff around a Bash command (bashEditDiff).

The diff is "what changed in the working tree while the command ran", so it also catches edits by
other processes, such as a second Claude session in the same repo. An event is attributed to the
command only when the command text names the file; otherwise it carries a "maybe another process" note.
"""
import os

from fileview.capture.context import HookContext
from fileview.model.event import Event
from fileview.model.kind import Kind

UNATTRIBUTED = "changed during command, maybe another process"


def bash_diff_events(ctx: HookContext, command: str, response) -> list[Event]:
    diff = response.get("bashEditDiff") if isinstance(response, dict) else None
    if not isinstance(diff, dict):
        return []
    events, listed = [], set()
    for entry in diff.get("files") or []:
        path = entry.get("filePath") or ""
        listed.add(path)
        kind = Kind.DELETE if entry.get("deleted") else Kind.CREATE if entry.get("created") else Kind.WRITE
        events.append(ctx.event(kind, path, _attribution(command, path)))
    for path in diff.get("changedFiles") or []:
        if path not in listed:
            events.append(ctx.event(Kind.WRITE, path, _attribution(command, path)))
    more = diff.get("moreFiles") or 0
    if more:
        events.append(ctx.event(Kind.WRITE, "", f"... +{more} more files"))
    return events


def _attribution(command: str, path: str) -> str:
    return "" if os.path.basename(path) in command else UNATTRIBUTED
