"""ignore / deignore: path glob and regex shorthands, plus full match blocks (kind / command / path)."""
from fileview.config import fields
from fileview.config.sections import checks, match
from fileview.rules.model import PatternSet


def parse(document: dict, path: str) -> PatternSet:
    fields.expect_keys(document, ("glob", "regex", "match"), path)
    regex = fields.strings(document, "regex", path, default=[])
    for i, pattern in enumerate(regex):
        checks.regex(pattern, f"{path}.regex[{i}]")
    matches = tuple(match.parse(item, item_path) for item_path, item in fields.sections(document, "match", path, default=[]))
    return PatternSet(glob=fields.strings(document, "glob", path, default=[]), regex=regex, match=matches)


def dump(patterns: PatternSet) -> dict:
    return {"glob": list(patterns.glob), "regex": list(patterns.regex), "match": [match.dump(m) for m in patterns.match]}
