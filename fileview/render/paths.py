"""Fit a path into a width by cutting its middle, so the file name always stays visible."""
import os

ELLIPSIS = "…"


def elide_middle(text: str, max_width: int) -> str:
    if len(text) <= max_width or max_width < 8:
        return text
    head, _, name = text.rpartition(os.sep)
    keep_tail = os.sep + name if head else name
    room = max_width - len(keep_tail) - len(ELLIPSIS)
    if room < 4:                                   # even the file name is too long: cut its middle
        half = (max_width - len(ELLIPSIS)) // 2
        return text[:half] + ELLIPSIS + text[-(max_width - len(ELLIPSIS) - half):]
    return head[:room] + ELLIPSIS + keep_tail
