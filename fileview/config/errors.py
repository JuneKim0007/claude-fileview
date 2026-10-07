"""A config problem as data: a stable code, the file, the dotted path inside it, and the detail.
The same value is printed by the CLI, shown in the viewer, and (later) returned by an MCP tool."""
from dataclasses import asdict, dataclass


@dataclass
class ConfigError(Exception):
    code: str             # missing_file, unreadable_yaml, not_a_mapping, missing_field, wrong_type, ...
    file: str = ""
    path: str = ""        # dotted location inside the document, e.g. "ignore.glob[2]"
    detail: str = ""

    def __str__(self) -> str:
        where = f"{self.file} at {self.path}" if self.path else self.file
        return f"{self.code}: {where}" + (f": {self.detail}" if self.detail else "")

    def as_dict(self) -> dict:
        return asdict(self)
