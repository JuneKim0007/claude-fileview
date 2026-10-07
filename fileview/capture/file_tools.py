"""Events from Claude Code's file tools: Read, Write, Edit, MultiEdit, NotebookEdit, Grep, Glob."""
import os

from fileview.capture.context import HookContext
from fileview.model.event import Event
from fileview.model.kind import Kind

FILE_TOOLS = {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Grep", "Glob"}


def file_tool_events(ctx: HookContext, tool: str, tool_input: dict, response) -> list[Event]:
    path = _absolute(ctx.cwd, tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    if tool == "Read":
        return [ctx.event(Kind.READ, path, _line_range(tool_input))]
    if tool == "Write":
        created = isinstance(response, dict) and response.get("type") == "create"
        return [ctx.event(Kind.CREATE if created else Kind.WRITE, path)]
    if tool in ("Edit", "MultiEdit", "NotebookEdit"):
        return [ctx.event(Kind.WRITE, path)]
    if tool in ("Grep", "Glob"):
        where = _absolute(ctx.cwd, tool_input.get("path") or ".")
        return [ctx.event(Kind.SEARCH, where, f'"{tool_input.get("pattern", "")}"')]
    return []


def _line_range(tool_input: dict) -> str:
    offset, limit = tool_input.get("offset"), tool_input.get("limit")
    if offset is None and limit is None:
        return ""
    return f"lines {offset or 1}+{limit or 'all'}"


def _absolute(cwd: str, path: str) -> str:
    if not path:
        return ""
    return os.path.normpath(path if os.path.isabs(path) else os.path.join(cwd, path))
