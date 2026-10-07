"""colour: path colouring rules, each with exactly one of glob or regex; first match wins."""
from fileview.config import fields
from fileview.config.errors import ConfigError
from fileview.config.sections import checks
from fileview.rules.model import ColourRule


def parse(items: list[tuple[str, dict]], custom: dict) -> tuple[ColourRule, ...]:
    return tuple(_rule(path, item, custom) for path, item in items)


def dump(rules: tuple[ColourRule, ...]) -> list[dict]:
    return [{**({"glob": r.glob} if r.glob else {"regex": r.regex}), "colour": r.colour} for r in rules]


def _rule(path: str, item: dict, custom: dict) -> ColourRule:
    fields.expect_keys(item, ("glob", "regex", "colour"), path)
    glob = fields.string(item, "glob", path, default="")
    regex = fields.string(item, "regex", path, default="")
    if bool(glob) == bool(regex):
        raise ConfigError("wrong_type", path=path, detail="give exactly one of glob or regex")
    if regex:
        checks.regex(regex, f"{path}.regex")
    return ColourRule(colour=checks.colour(fields.colour(item, "colour", path), custom, f"{path}.colour"),
                      glob=glob, regex=regex)
