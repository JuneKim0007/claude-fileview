"""One logged activity, and its JSON-lines encoding."""
import json
from dataclasses import asdict, dataclass

from fileview.model.kind import Kind


@dataclass(frozen=True)
class Event:
    ts: float
    session: str
    agent: str
    kind: Kind
    path: str = ""      # absolute path when the event concerns one file
    detail: str = ""    # command, search pattern, line range or attribution note
    root: str = ""      # project root of the session that produced the event

    def to_json(self) -> str:
        data = asdict(self)
        data["kind"] = self.kind.value
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, line: str) -> "Event | None":
        try:
            data = json.loads(line)
            data["kind"] = Kind(data["kind"])
            return cls(**data)
        except (ValueError, KeyError, TypeError):
            return None
