"""Every filesystem location fileview reads or writes."""
import os
from pathlib import Path

HOME = Path.home()
CLAUDE_HOME = HOME / ".claude"
DEFAULT_STATE_DIR = CLAUDE_HOME / "fileview-state"
STATE_DIR = Path(os.environ.get("CLAUDE_FILEVIEW_STATE", DEFAULT_STATE_DIR))
VIEWERS_DIR = STATE_DIR / "viewers"
LOG_FILE = Path(os.environ.get("CLAUDE_FILEVIEW_LOG", STATE_DIR / "events.jsonl"))
CAPTURES_FILE = STATE_DIR / "captures.json"      # compiled from the rules file for the hook
TRANSCRIPTS_DIR = CLAUDE_HOME / "projects"
ENTRY_SCRIPT = CLAUDE_HOME / "fileview" / "bin" / "fileview"
SUPERVISOR_SOCKET = STATE_DIR / "supervisor.sock"
SUPERVISOR_LOCK = STATE_DIR / "supervisor.lock"
SUPERVISOR_LOG = STATE_DIR / "supervisor.log"
SUPERVISOR_STATE = STATE_DIR / "supervisor-sessions.json"
USER_CONFIG = HOME / ".config" / "claude-fileview" / "config.yaml"
DEFAULT_CONFIG = CLAUDE_HOME / "fileview" / "default.yaml"
