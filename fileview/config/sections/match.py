"""A match block, shared by ignore/deignore, announce and display:
  {kinds: [INVOKE, DONE], command: '^git push', glob: '*.md', regex: '...'}  (every field optional)"""
from fileview.config import fields
from fileview.config.errors import ConfigError
from fileview.config.sections import checks
from fileview.model.kind import Kind
from fileview.rules.model import Match

KEYS = ("kinds", "command", "glob", "regex")


def parse(document: dict, path: str) -> Match:
    fields.expect_keys(document, KEYS, path)
    kinds = fields.strings(document, "kinds", path, default=[])
    known = {kind.value for kind in Kind}
    for i, kind in enumerate(kinds):
        if kind not in known:
            raise ConfigError("unknown_kind", path=f"{path}.kinds[{i}]", detail=f"{kind!r}, known {sorted(known)}")
    command = fields.string(document, "command", path, default="")
    regex = fields.string(document, "regex", path, default="")
    if command:
        checks.regex(command, f"{path}.command")
    if regex:
        checks.regex(regex, f"{path}.regex")
    return Match(kinds=kinds, command=command, glob=fields.string(document, "glob", path, default=""), regex=regex)


def dump(match: Match) -> dict:
    document = {"kinds": list(match.kinds), "command": match.command, "glob": match.glob, "regex": match.regex}
    return {key: value for key, value in document.items() if value}
