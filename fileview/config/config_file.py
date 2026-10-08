"""One rules file on disk: read it into Rules (or raise ConfigError naming the file), write Rules to it
atomically, back it up before an overwrite."""
import shutil
import time
from pathlib import Path

from fileview.config import rules_document, yaml_codec
from fileview.config.atomic_write import atomic_write
from fileview.config.errors import ConfigError
from fileview.rules.model import Rules

HEADER = """# fileview rules. Reload a running viewer with `fileview reload`; check this file with `fileview config check`.
# visible = not matched by ignore, or matched by deignore. colour rules apply only to visible paths.
# colours: a name (green, blue, ...), a name from palette.colours, "#rrggbb", or 0-255.
"""


def read(path: Path) -> Rules:
    if not path.is_file():
        raise ConfigError("missing_file", str(path))
    document = yaml_codec.load(path.read_text(encoding="utf-8"), str(path))
    version = document.get("schemaVersion")
    if version is None:
        raise ConfigError("missing_field", str(path), "schemaVersion")
    if version != rules_document.SCHEMA_VERSION:
        raise ConfigError("unsupported_schema_version", str(path), "schemaVersion",
                          f"{version!r}, this build reads {rules_document.SCHEMA_VERSION}")
    try:
        return rules_document.parse(document)
    except ConfigError as failure:
        failure.file = str(path)
        raise


def write(path: Path, rules: Rules) -> Path:
    atomic_write(path, HEADER + yaml_codec.dump(rules_document.of(rules)))
    return path


def backup(path: Path) -> Path:
    target = path.with_name(f"{path.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(path, target)
    return target
