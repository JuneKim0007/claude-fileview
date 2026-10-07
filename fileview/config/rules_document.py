"""Schema version 1 of the rules file: parse(document) -> Rules and of(Rules) -> document, so the
default file is generated from the same code that reads it. Sections are optional; a missing one
means "nothing" except palette, which falls back to the built-in palette."""
import re

from fileview.config import fields
from fileview.config.errors import ConfigError
from fileview.model.kind import Kind
from fileview.rules.colours import sgr
from fileview.rules.defaults import DEFAULT_RULES
from fileview.rules.model import ColourRule, PaletteSpec, PatternSet, Prefix, Rules

SCHEMA_VERSION = 1
SECTIONS = ("schemaVersion", "palette", "prefixes", "ignore", "deignore", "colour")


def parse(document: dict) -> Rules:
    fields.expect_keys(document, SECTIONS, "")
    palette = _palette(fields.section(document, "palette", "", default={}))
    custom = palette.colours
    return Rules(
        palette=palette,
        prefixes=tuple(_prefix(path, item, custom) for path, item in fields.sections(document, "prefixes", "", default=[])),
        ignore=_patterns(fields.section(document, "ignore", "", default={}), "ignore"),
        deignore=_patterns(fields.section(document, "deignore", "", default={}), "deignore"),
        colour=tuple(_colour_rule(path, item, custom) for path, item in fields.sections(document, "colour", "", default=[])),
    )


def of(rules: Rules) -> dict:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "palette": {"kinds": dict(rules.palette.kinds), "label": rules.palette.label,
                    "colours": dict(rules.palette.colours)},
        "prefixes": [{"path": p.path, "label": p.label, **({"colour": p.colour} if p.colour != "" else {})}
                     for p in rules.prefixes],
        "ignore": {"glob": list(rules.ignore.glob), "regex": list(rules.ignore.regex)},
        "deignore": {"glob": list(rules.deignore.glob), "regex": list(rules.deignore.regex)},
        "colour": [{**({"glob": r.glob} if r.glob else {"regex": r.regex}), "colour": r.colour} for r in rules.colour],
    }


def _palette(document: dict) -> PaletteSpec:
    fields.expect_keys(document, ("kinds", "label", "colours"), "palette")
    custom_doc = fields.section(document, "colours", "palette", default={})
    custom = {name: fields.colour(custom_doc, name, "palette.colours") for name in custom_doc}
    for name, value in custom.items():
        _check_colour(value, {}, f"palette.colours.{name}")
    kinds_doc = fields.section(document, "kinds", "palette", default={})
    fields.expect_keys(kinds_doc, tuple(kind.value for kind in Kind), "palette.kinds")
    kinds = dict(DEFAULT_RULES.palette.kinds)
    for name in kinds_doc:
        kinds[name] = _check_colour(fields.colour(kinds_doc, name, "palette.kinds"), custom, f"palette.kinds.{name}")
    label = _check_colour(fields.colour(document, "label", "palette", default=DEFAULT_RULES.palette.label),
                          custom, "palette.label")
    return PaletteSpec(kinds=kinds, label=label, colours=custom)


def _prefix(path: str, item: dict, custom: dict) -> Prefix:
    fields.expect_keys(item, ("path", "label", "colour"), path)
    colour = fields.colour(item, "colour", path, default="")
    if colour != "":
        _check_colour(colour, custom, f"{path}.colour")
    return Prefix(fields.string(item, "path", path), fields.string(item, "label", path), colour)


def _patterns(document: dict, path: str) -> PatternSet:
    fields.expect_keys(document, ("glob", "regex"), path)
    regex = fields.strings(document, "regex", path, default=[])
    for i, pattern in enumerate(regex):
        _check_regex(pattern, f"{path}.regex[{i}]")
    return PatternSet(glob=fields.strings(document, "glob", path, default=[]), regex=regex)


def _colour_rule(path: str, item: dict, custom: dict) -> ColourRule:
    fields.expect_keys(item, ("glob", "regex", "colour"), path)
    glob = fields.string(item, "glob", path, default="")
    regex = fields.string(item, "regex", path, default="")
    if bool(glob) == bool(regex):
        raise ConfigError("wrong_type", path=path, detail="give exactly one of glob or regex")
    if regex:
        _check_regex(regex, f"{path}.regex")
    return ColourRule(colour=_check_colour(fields.colour(item, "colour", path), custom, f"{path}.colour"),
                      glob=glob, regex=regex)


def _check_colour(value, custom: dict, path: str):
    try:
        sgr(value, custom)
    except ValueError as failure:
        raise ConfigError("unknown_colour", path=path, detail=str(failure)) from failure
    return value


def _check_regex(pattern: str, path: str) -> None:
    try:
        re.compile(pattern)
    except re.error as failure:
        raise ConfigError("bad_regex", path=path, detail=f"{pattern!r}: {failure}") from failure
