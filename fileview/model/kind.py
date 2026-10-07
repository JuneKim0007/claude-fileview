"""The kinds of file activity the log records."""
from enum import Enum


class Kind(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    CREATE = "CREATE"
    DELETE = "DELETE"
    SEARCH = "SEARCH"
    INVOKE = "INVOKE"
    LOAD = "LOAD"
