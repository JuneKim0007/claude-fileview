"""announce / display: {match: {...}, text: "<yellow>pushed</> {push.new}"}. The template is checked at
load: every <colour> must resolve and every {placeholder} must be a base value or a group some
capture provides, so a typo is a config error, not a silently empty banner."""
from fileview.config import fields
from fileview.config.errors import ConfigError
from fileview.config.sections import checks, match
from fileview.rules.model import CaptureRule, TextRule
from fileview.rules.template import BASE_VALUES, capture_fields, parse


def parse_rules(items: list[tuple[str, dict]], custom: dict, captures: tuple[CaptureRule, ...]) -> tuple[TextRule, ...]:
    known = set(BASE_VALUES)
    for capture in captures:
        known |= capture_fields(capture.name, capture.command, capture.output)
    return tuple(_rule(path, item, custom, known) for path, item in items)


def dump(rules: tuple[TextRule, ...]) -> list[dict]:
    return [{"match": match.dump(r.match), "text": r.text} for r in rules]


def _rule(path: str, item: dict, custom: dict, known: set[str]) -> TextRule:
    fields.expect_keys(item, ("match", "text"), path)
    text = fields.string(item, "text", path)
    template = parse(text)
    for colour in sorted(template.colours()):
        checks.colour(colour, custom, f"{path}.text")
    unknown = sorted(template.placeholders() - known)
    if unknown:
        raise ConfigError("unknown_placeholder", path=f"{path}.text", detail=f"{unknown}, known {sorted(known)}")
    return TextRule(match.parse(fields.section(item, "match", path, default={}), f"{path}.match"), text)
