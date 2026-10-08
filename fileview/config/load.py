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

    return _Loader(config_file, confirm, default_config).load(lookup.choose(explicit, user_config))


class _Loader:
    """One load: the file module, the confirm port and the default file stay fixed; result fills in."""

    def __init__(self, config_file, confirm: Confirm | None, default_config: Path) -> None:
        self.files, self.confirm, self.default_config = config_file, confirm, default_config
        self.result = LoadedRules(DEFAULT_RULES, "built-in defaults")

    def load(self, choice) -> LoadedRules:
        if not choice.path.is_file() and choice.generated_when_missing:
            self.files.write(choice.path, self._default_rules()[0])
            self.result.notes.append(f"generated {choice.path} from the defaults")
        rules = self._read_or_repair(choice.path, choice.origin)
        if rules is not None:
            self.result.rules, self.result.source = rules, str(choice.path)
        else:
            self.result.rules, self.result.source = self._default_rules()
        return self.result

    def _read_or_repair(self, path: Path, origin: str) -> Rules | None:
        try:
            return self.files.read(path)
        except ConfigError as problem:
            self.result.problems.append(problem)
            if problem.code == "missing_file":
                self.result.notes.append(f"{origin} file {path} not found; using the default file")
                return None
        question = f"{self.result.problems[-1]}\nBack up {path} and regenerate it from the defaults?"
        if not (self.confirm(question) if self.confirm else None):
            self.result.notes.append(f"kept {path} unchanged; fix it, or run: fileview config init --force")
            return None
        saved = self.files.backup(path)
        self.files.write(path, DEFAULT_RULES)
        self.result.notes.append(f"backed up to {saved} and regenerated {path}")
        return DEFAULT_RULES

    def _default_rules(self) -> tuple[Rules, str]:
        if not self.default_config.is_file():
            self.files.write(self.default_config, DEFAULT_RULES)
            self.result.notes.append(f"generated {self.default_config}")
        rules = self._read_or_repair(self.default_config, "default")
        return (rules, str(self.default_config)) if rules is not None else (DEFAULT_RULES, "built-in defaults")
