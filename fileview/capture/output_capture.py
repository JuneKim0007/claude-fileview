"""Named groups from a finished command, as "<capture>.<group>" values. Only named groups are kept,
so raw output never reaches the log; only the tail of the output is scanned, bounding regex cost."""
from fileview.capture.compiled_captures import CompiledCapture

SCAN_CHARS = 64 * 1024


def capture_values(command: str, output: str, captures: list[CompiledCapture]) -> dict[str, str]:
    tail = output[-SCAN_CHARS:]
    values: dict[str, str] = {}
    for capture in captures:
        command_match = capture.command.search(command)
        if command_match is None:
            continue
        found = dict(command_match.groupdict())
        if capture.output is not None:
            output_match = capture.output.search(tail)
            if output_match is None:
                continue                      # the output pattern is part of the condition
            found.update(output_match.groupdict())
        values.update({f"{capture.name}.{group}": text for group, text in found.items() if text is not None})
    return values


def output_text(response) -> str:
    """stdout and stderr of a Bash tool response (git push reports on stderr)."""
    if isinstance(response, dict):
        return "\n".join(str(response.get(key) or "") for key in ("stdout", "stderr"))
    return str(response or "")
