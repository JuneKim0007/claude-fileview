"""palette: colours per kind, the default label colour, and custom colour names."""
from fileview.config import fields
from fileview.config.sections import checks
from fileview.model.kind import Kind
from fileview.rules.defaults import DEFAULT_RULES
from fileview.rules.model import PaletteSpec


def parse(document: dict) -> PaletteSpec:
    fields.expect_keys(document, ("kinds", "label", "colours"), "palette")
    custom_doc = fields.section(document, "colours", "palette", default={})
    custom = {name: fields.colour(custom_doc, name, "palette.colours") for name in custom_doc}
    for name, value in custom.items():
        checks.colour(value, {}, f"palette.colours.{name}")
    kinds_doc = fields.section(document, "kinds", "palette", default={})
    fields.expect_keys(kinds_doc, tuple(kind.value for kind in Kind), "palette.kinds")
    kinds = dict(DEFAULT_RULES.palette.kinds)
    for name in kinds_doc:
        kinds[name] = checks.colour(fields.colour(kinds_doc, name, "palette.kinds"), custom, f"palette.kinds.{name}")
    label = checks.colour(fields.colour(document, "label", "palette", default=DEFAULT_RULES.palette.label),
                          custom, "palette.label")
    return PaletteSpec(kinds=kinds, label=label, colours=custom)


def dump(spec: PaletteSpec) -> dict:
    return {"kinds": dict(spec.kinds), "label": spec.label, "colours": dict(spec.colours)}
