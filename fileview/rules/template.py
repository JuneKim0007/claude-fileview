"""The template language: "<yellow>git pushed</> {push.branch}". <colour> opens a colour, </> resets,
{name} is a value; {{ }} << >> are literal braces and angle brackets. A template is parsed into parts
once; values are inserted as plain text at draw time and never re-parsed, so a command or output
containing "<red>" or "{x}" cannot inject markup."""
import re
from dataclasses import dataclass
from functools import lru_cache

TOKEN = re.compile(r"\{\{|\}\}|<<|>>|</>|<([A-Za-z0-9#_]+)>|\{([A-Za-z_][\w.]*)\}")
LITERALS = {"{{": "{", "}}": "}", "<<": "<", ">>": ">"}
BASE_VALUES = frozenset({"command", "path", "kind", "agent", "session"})


@dataclass(frozen=True)
class Part:
    kind: str           # "text", "value", "colour", "reset"
    data: str = ""


@dataclass(frozen=True)
class Template:
    parts: tuple[Part, ...]

    def placeholders(self) -> set[str]:
        return {p.data for p in self.parts if p.kind == "value"}

    def colours(self) -> set[str]:
        return {p.data for p in self.parts if p.kind == "colour"}

    def fill(self, values: dict[str, str]) -> "tuple[Part, ...] | None":
        """Parts with values substituted as text; None when any placeholder has no value."""
        if not self.placeholders() <= values.keys():
            return None
        return tuple(Part("text", values[p.data]) if p.kind == "value" else p for p in self.parts)


@lru_cache(maxsize=256)
def parse(text: str) -> Template:
    parts, position = [], 0
    for token in TOKEN.finditer(text):
        if token.start() > position:
            parts.append(Part("text", text[position:token.start()]))
        raw = token.group(0)
        if raw in LITERALS:
            parts.append(Part("text", LITERALS[raw]))
        elif raw == "</>":
            parts.append(Part("reset"))
        elif token.group(1):
            parts.append(Part("colour", token.group(1)))
        else:
            parts.append(Part("value", token.group(2)))
        position = token.end()
    if position < len(text):
        parts.append(Part("text", text[position:]))
    return Template(tuple(parts))


def capture_fields(name: str, *patterns: str) -> set[str]:
    """The "<name>.<group>" values a capture can provide, from its patterns' named groups."""
    return {f"{name}.{group}" for pattern in patterns if pattern for group in re.compile(pattern).groupindex}
