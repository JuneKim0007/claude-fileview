"""prefixes: directory -> [label], with an optional highlight colour per label."""
from fileview.config import fields
from fileview.config.sections import checks
from fileview.rules.model import Prefix


def parse(items: list[tuple[str, dict]], custom: dict) -> tuple[Prefix, ...]:
    return tuple(_prefix(path, item, custom) for path, item in items)


def dump(prefixes: tuple[Prefix, ...]) -> list[dict]:
    return [{"path": p.path, "label": p.label, **({"colour": p.colour} if p.colour != "" else {})} for p in prefixes]


def _prefix(path: str, item: dict, custom: dict) -> Prefix:
    fields.expect_keys(item, ("path", "label", "colour"), path)
    colour = fields.colour(item, "colour", path, default="")
    if colour != "":
        checks.colour(colour, custom, f"{path}.colour")
    return Prefix(fields.string(item, "path", path), fields.string(item, "label", path), colour)
