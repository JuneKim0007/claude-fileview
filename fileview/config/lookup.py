"""Which rules file to read: --config, then $CLAUDE_FILEVIEW_CONFIG, then the user file. The shipped
default file is the fallback, never a lookup candidate."""
import os
from dataclasses import dataclass
from pathlib import Path

from fileview.locations import USER_CONFIG

ENV_VARIABLE = "CLAUDE_FILEVIEW_CONFIG"


@dataclass(frozen=True)
class Choice:
    path: Path
    origin: str           # "--config", "$CLAUDE_FILEVIEW_CONFIG" or "user"

    @property
    def generated_when_missing(self) -> bool:
        return self.origin == "user"     # only the user file is created on demand


def choose(explicit: str | None = None, user_config: Path = USER_CONFIG) -> Choice:
    if explicit:
        return Choice(Path(explicit).expanduser().resolve(), "--config")
    if os.environ.get(ENV_VARIABLE):
        return Choice(Path(os.environ[ENV_VARIABLE]).expanduser().resolve(), f"${ENV_VARIABLE}")
    return Choice(user_config, "user")
