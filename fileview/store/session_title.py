"""Session id prefix -> the title Claude Code gave the session (latest "ai-title" transcript entry).
The title appears only after the first exchange, so callers poll; reads are cached on file mtime."""
import json
import os
from pathlib import Path

from fileview.locations import TRANSCRIPTS_DIR

TAIL_BYTES = 512 * 1024
_cache: dict[str, tuple[float, str | None]] = {}


def session_title(session_prefix: str) -> str | None:
    transcript = _transcript(session_prefix)
    if transcript is None:
        return None
    mtime = transcript.stat().st_mtime
    cached = _cache.get(session_prefix)
    if cached and cached[0] == mtime:
        return cached[1]
    title = _latest_title(transcript)
    _cache[session_prefix] = (mtime, title)
    return title


def _transcript(session_prefix: str) -> Path | None:
    matches = sorted(TRANSCRIPTS_DIR.glob(f"*/{session_prefix}*.jsonl"), key=os.path.getmtime)
    return matches[-1] if matches else None


def _latest_title(transcript: Path) -> str | None:
    with open(transcript, "rb") as handle:
        handle.seek(max(0, transcript.stat().st_size - TAIL_BYTES))
        lines = handle.read().splitlines()
    for raw in reversed(lines):
        if b'"ai-title"' not in raw:
            continue
        try:
            return json.loads(raw).get("aiTitle") or None
        except ValueError:
            continue
    return None
