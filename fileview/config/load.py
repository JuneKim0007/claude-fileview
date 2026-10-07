"""The fallback policy: which Rules a viewer runs with, where they came from, and what went wrong.

  chosen file present and valid      -> use it
  user file missing                  -> generate it from the defaults, use it
  --config / env file missing        -> report, use the default file
  chosen file malformed              -> report; ask (if a confirm port is given) to back up and
                                        regenerate it; otherwise use the default file this time
  default file missing               -> generate it; malformed -> report, ask to regenerate, else built-ins
  PyYAML missing                     -> report, built-ins
Nothing is ever overwritten without a "yes" from the confirm port."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from fileview.config.errors import ConfigError
from fileview.locations import DEFAULT_CONFIG, USER_CONFIG
from fileview.rules.defaults import DEFAULT_RULES
from fileview.rules.model import Rules

Confirm = Callable[[str], bool | None]      # None: nobody could be asked


@dataclass
class LoadedRules:
    rules: Rules
    source: str                             # file path, or "built-in defaults"
    problems: list[ConfigError] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"source": self.source, "problems": [p.as_dict() for p in self.problems], "notes": self.notes}


def load_rules(explicit: str | None = None, confirm: Confirm | None = None,
               user_config: Path = USER_CONFIG, default_config: Path = DEFAULT_CONFIG) -> LoadedRules:
    try:
        from fileview.config import config_file, lookup
    except ImportError as failure:          # PyYAML absent (e.g. after a Python upgrade)
        problem = ConfigError("missing_dependency", "PyYAML", detail=f"{failure}; install pyyaml for this python")
        return LoadedRules(DEFAULT_RULES, "built-in defaults", [problem])

    result = LoadedRules(DEFAULT_RULES, "built-in defaults")
    choice = lookup.choose(explicit, user_config)
    if not choice.path.is_file() and choice.generated_when_missing:
        config_file.write(choice.path, _default_rules(config_file, default_config, result, confirm)[0])
        result.notes.append(f"generated {choice.path} from the defaults")
    rules = _read_or_repair(config_file, choice.path, choice.origin, result, confirm)
    if rules is not None:
        result.rules, result.source = rules, str(choice.path)
        return result
    result.rules, result.source = _default_rules(config_file, default_config, result, confirm)
    return result


def _read_or_repair(config_file, path: Path, origin: str, result: LoadedRules, confirm: Confirm | None) -> Rules | None:
    try:
        return config_file.read(path)
    except ConfigError as problem:
        result.problems.append(problem)
        if problem.code == "missing_file":
            result.notes.append(f"{origin} file {path} not found; using the default file")
            return None
    answer = confirm(f"{result.problems[-1]}\nBack up {path} and regenerate it from the defaults?") if confirm else None
    if not answer:
        result.notes.append(f"kept {path} unchanged; fix it, or run: fileview config init --force")
        return None
    saved = config_file.backup(path)
    config_file.write(path, DEFAULT_RULES)
    result.notes.append(f"backed up to {saved} and regenerated {path}")
    return DEFAULT_RULES


def _default_rules(config_file, default_config: Path, result: LoadedRules,
                   confirm: Confirm | None) -> tuple[Rules, str]:
    if not default_config.is_file():
        config_file.write(default_config, DEFAULT_RULES)
        result.notes.append(f"generated {default_config}")
    rules = _read_or_repair(config_file, default_config, "default", result, confirm)
    return (rules, str(default_config)) if rules is not None else (DEFAULT_RULES, "built-in defaults")
