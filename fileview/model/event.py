"""One logged activity, and its JSON-lines encoding."""
import json
from dataclasses import asdict, dataclass, field

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
    values: dict[str, str] = field(default_factory=dict)   # "<capture>.<group>" -> text, DONE/FAILED only

    def to_json(self) -> str:
        data = asdict(self)
        data["kind"] = self.kind.value
        if not self.values:
            del data["values"]          # keep ordinary lines as small as before
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, line: str) -> "Event | None":
        try:
            data = json.loads(line)
            data["kind"] = Kind(data["kind"])
            return cls(**data)
        except (ValueError, KeyError, TypeError):
            return None
