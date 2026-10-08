"""The wire format between clients, viewers and the supervisor: one JSON object per line over a Unix
socket. Every request carries the code version, so a supervisor running older code is detected
(the way Gradle refuses an incompatible daemon) instead of silently serving stale behaviour."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent
SESSION_KEY_LENGTH = 8


def session_key(session_id: str | None) -> str:
    """The prefix of a Claude Code session id that names its viewer in records, the table and messages."""
    return (session_id or "")[:SESSION_KEY_LENGTH]


@lru_cache(maxsize=1)
def code_version() -> str:
    digest = hashlib.sha1()
    for source in sorted(PACKAGE_DIR.rglob("*.py")):
        digest.update(source.relative_to(PACKAGE_DIR).as_posix().encode())
        digest.update(source.read_bytes())
    return digest.hexdigest()[:12]


def encode(message: dict) -> bytes:
    return (json.dumps(message, separators=(",", ":")) + "\n").encode()


def decode_request(line: bytes) -> dict:
    """A request ({"op": ...}): what the supervisor reads, and what it pushes down a viewer link."""
    return _decode(line, "op")


def decode_response(line: bytes) -> dict:
    """A response ({"ok": ...}): what a client or an attaching viewer reads back."""
    return _decode(line, "ok")


def _decode(line: bytes, required: str) -> dict:
    message = json.loads(line)
    if not isinstance(message, dict) or required not in message:
        raise ValueError(f"not a protocol message: no {required!r}")
    return message


def ok(**fields) -> dict:
    return {"ok": True, **fields}


def error(reason: str, **fields) -> dict:
    return {"ok": False, "error": reason, **fields}
