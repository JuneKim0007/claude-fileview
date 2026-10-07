"""Hook entry: payload on stdin -> events appended to the log. Swallows every error and returns 0,
because a hook that fails can block Claude's tool calls."""
import json
import os
import sys

from fileview.capture.bash_diff import bash_diff_events
from fileview.capture.bash_reads import bash_read_events
from fileview.capture.compiled_captures import load as load_captures
from fileview.capture.context import HookContext
from fileview.capture.file_tools import FILE_TOOLS, file_tool_events
from fileview.capture.output_capture import capture_values, output_text
from fileview.model.event import Event
from fileview.model.kind import Kind


def events_for(payload: dict) -> list[Event]:
    ctx = HookContext.from_payload(payload)
    hook = payload.get("hook_event_name")
    tool = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    response = payload.get("tool_response")
    if hook == "PreToolUse" and tool == "Bash":
        return [ctx.event(Kind.INVOKE, "", tool_input.get("command") or "")]
    if hook == "PostToolUse" and tool in FILE_TOOLS:
        return file_tool_events(ctx, tool, tool_input, response)
    if hook == "PostToolUse" and tool == "Bash":
        command = tool_input.get("command") or ""
        done = ctx.event(Kind.DONE, "", command, capture_values(command, output_text(response), load_captures()))
        return bash_diff_events(ctx, command, response) + bash_read_events(ctx, command) + [done]
    if hook == "PostToolUseFailure" and tool == "Bash":
        command = tool_input.get("command") or ""
        output = f"{payload.get('error') or ''}\n{output_text(response)}"
        return [ctx.event(Kind.FAILED, "", command, capture_values(command, output, load_captures()))]
    if hook == "InstructionsLoaded":
        path = payload.get("file_path") or ""
        detail = "" if path else json.dumps({k: v for k, v in payload.items() if k != "transcript_path"})[:200]
        return [ctx.event(Kind.LOAD, os.path.abspath(path) if path else "", detail)]
    return []


def run() -> int:
    try:
        from fileview.store.writer import append
        append(events_for(json.load(sys.stdin)))
    except Exception:   # noqa: BLE001 - a logging hook must never fail the tool call
        pass
    return 0
