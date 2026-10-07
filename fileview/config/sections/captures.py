"""captures: named groups to keep from finished commands. Names are unique identifiers, since templates
refer to "<name>.<group>"."""
import re

from fileview.config import fields
from fileview.config.errors import ConfigError
from fileview.config.sections import checks
from fileview.rules.model import CaptureRule

NAME = re.compile(r"[A-Za-z_]\w*")


def parse(items: list[tuple[str, dict]]) -> tuple[CaptureRule, ...]:
    rules, seen = [], set()
    for path, item in items:
        fields.expect_keys(item, ("name", "command", "output"), path)
        name = fields.string(item, "name", path)
        if not NAME.fullmatch(name):
            raise ConfigError("wrong_type", path=f"{path}.name", detail=f"{name!r} must be an identifier")
        if name in seen:
            raise ConfigError("duplicate_name", path=f"{path}.name", detail=repr(name))
        seen.add(name)
        command = checks.regex(fields.string(item, "command", path), f"{path}.command")
        output = fields.string(item, "output", path, default="")
        if output:
            checks.regex(output, f"{path}.output")
        rules.append(CaptureRule(name, command, output))
    return tuple(rules)


def dump(rules: tuple[CaptureRule, ...]) -> list[dict]:
    return [{"name": r.name, "command": r.command, **({"output": r.output} if r.output else {})} for r in rules]
