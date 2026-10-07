"""The kinds of activity the log records. DONE and FAILED close a Bash command (PostToolUse /
PostToolUseFailure) and carry values captured from its output."""
from enum import Enum


class Kind(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    CREATE = "CREATE"
    DELETE = "DELETE"
    SEARCH = "SEARCH"
    INVOKE = "INVOKE"
    DONE = "DONE"
    FAILED = "FAILED"
    LOAD = "LOAD"
