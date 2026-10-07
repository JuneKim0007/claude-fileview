"""Schema version 1 of the rules file, composed from one parser per section (config/sections/):
parse(document) -> Rules and of(Rules) -> document, so the default file is generated from the same
code that reads it. Sections are optional; a missing one means "nothing" except palette, which
falls back to the built-in palette."""
from fileview.config import fields
from fileview.config.sections import captures, colour, palette, prefixes, texts, visibility
from fileview.rules.model import Rules

SCHEMA_VERSION = 1
SECTIONS = ("schemaVersion", "palette", "prefixes", "ignore", "deignore", "colour", "captures", "announce", "display")


def parse(document: dict) -> Rules:
    fields.expect_keys(document, SECTIONS, "")
    spec = palette.parse(fields.section(document, "palette", "", default={}))
    capture_rules = captures.parse(fields.sections(document, "captures", "", default=[]))
    return Rules(
        palette=spec,
        prefixes=prefixes.parse(fields.sections(document, "prefixes", "", default=[]), spec.colours),
        ignore=visibility.parse(fields.section(document, "ignore", "", default={}), "ignore"),
        deignore=visibility.parse(fields.section(document, "deignore", "", default={}), "deignore"),
        colour=colour.parse(fields.sections(document, "colour", "", default=[]), spec.colours),
        captures=capture_rules,
        announce=texts.parse_rules(fields.sections(document, "announce", "", default=[]), spec.colours, capture_rules),
        display=texts.parse_rules(fields.sections(document, "display", "", default=[]), spec.colours, capture_rules),
    )


def of(rules: Rules) -> dict:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "palette": palette.dump(rules.palette),
        "prefixes": prefixes.dump(rules.prefixes),
        "ignore": visibility.dump(rules.ignore),
        "deignore": visibility.dump(rules.deignore),
        "colour": colour.dump(rules.colour),
        "captures": captures.dump(rules.captures),
        "announce": texts.dump(rules.announce),
        "display": texts.dump(rules.display),
    }
