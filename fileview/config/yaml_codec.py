"""YAML text <-> a mapping. Safe loading only; duplicate keys are rejected (PyYAML would silently keep
the last one); the document must be a mapping. Syntax errors carry their line and column."""
import yaml

from fileview.config.errors import ConfigError


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _mapping_without_duplicates(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(None, None, f"duplicate key {key!r}", key_node.start_mark)
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping_without_duplicates)


def load(text: str, file: str) -> dict:
    try:
        document = yaml.load(text, Loader=_UniqueKeyLoader)    # noqa: S506 - a SafeLoader subclass
    except yaml.MarkedYAMLError as failure:
        mark = failure.problem_mark
        where = f"line {mark.line + 1}, column {mark.column + 1}: " if mark else ""
        raise ConfigError("unreadable_yaml", file, detail=where + (failure.problem or str(failure))) from failure
    except yaml.YAMLError as failure:
        raise ConfigError("unreadable_yaml", file, detail=str(failure)) from failure
    if not isinstance(document, dict):
        raise ConfigError("not_a_mapping", file, detail="the document is not a set of key: value entries")
    return document


def dump(document: dict) -> str:
    return yaml.safe_dump(document, sort_keys=False, default_flow_style=None, allow_unicode=True, indent=2, width=100)
