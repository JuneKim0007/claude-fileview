"""The wire format between clients, viewers and the supervisor: one JSON object per line over a Unix
socket. Every request carries the code version, so a supervisor running older code is detected
(the way Gradle refuses an incompatible daemon) instead of silently serving stale behaviour."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def code_version() -> str:
    digest = hashlib.sha1()
    for source in sorted(PACKAGE_DIR.rglob("*.py")):
        digest.update(source.relative_to(PACKAGE_DIR).as_posix().encode())
        digest.update(source.read_bytes())
    return digest.hexdigest()[:12]


def encode(message: dict) -> bytes:
    return (json.dumps(message, separators=(",", ":")) + "\n").encode()


def decode(line: bytes) -> dict:
    message = json.loads(line)
    if not isinstance(message, dict) or "op" not in message and "ok" not in message:
        raise ValueError("not a protocol message")
    return message


def ok(**fields) -> dict:
    return {"ok": True, **fields}


def error(reason: str, **fields) -> dict:
    return {"ok": False, "error": reason, **fields}
