"""Typed reads from a parsed document. Every failure names its dotted path and a stable code
(missing_field, wrong_type, unknown_keys); the file is added by the caller."""
from fileview.config.errors import ConfigError

_MISSING = object()


def section(document: dict, key: str, path: str, default=_MISSING) -> dict:
    value = _field(document, key, path, default)
    return _typed(value, dict, _join(path, key), "a mapping")


def string(document: dict, key: str, path: str, default=_MISSING) -> str:
    return _typed(_field(document, key, path, default), str, _join(path, key), "a string")


def strings(document: dict, key: str, path: str, default=_MISSING) -> tuple[str, ...]:
    items = _typed(_field(document, key, path, default), list, _join(path, key), "a list")
    return tuple(_typed(item, str, f"{_join(path, key)}[{i}]", "a string") for i, item in enumerate(items))


def sections(document: dict, key: str, path: str, default=_MISSING) -> list[tuple[str, dict]]:
    """A list of mappings, each paired with its own dotted path."""
    items = _typed(_field(document, key, path, default), list, _join(path, key), "a list")
    return [(f"{_join(path, key)}[{i}]", _typed(item, dict, f"{_join(path, key)}[{i}]", "a mapping"))
            for i, item in enumerate(items)]


def colour(document: dict, key: str, path: str, default=_MISSING) -> str | int:
    value = _field(document, key, path, default)
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ConfigError("wrong_type", path=_join(path, key), detail="expected a colour name, #rrggbb or 0-255")
    return value


def expect_keys(document: dict, allowed: tuple[str, ...], path: str) -> None:
    unknown = [key for key in document if key not in allowed]
    if unknown:
        raise ConfigError("unknown_keys", path=path or "(top level)", detail=f"{unknown}, known {list(allowed)}")


def _field(document: dict, key: str, path: str, default):
    if key in document and document[key] is not None:
        return document[key]
    if default is not _MISSING:
        return default
    raise ConfigError("missing_field", path=_join(path, key))


def _typed(value, kind: type, path: str, expected: str):
    if isinstance(value, bool) and kind is not bool or not isinstance(value, kind):
        raise ConfigError("wrong_type", path=path, detail=f"expected {expected}, got {type(value).__name__}")
    return value


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key
