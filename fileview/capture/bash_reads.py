"""READ events inferred from a Bash command: arguments of read-type programs that are existing files.

Inference, not observation: the harness reports only the command text for reads. The command is split
into simple commands; `cd DIR` moves the base directory for the commands after it, so
`cd backend && cat Makefile` resolves to backend/Makefile.
"""
import os
import shlex

from fileview.capture.context import HookContext
from fileview.model.event import Event
from fileview.model.kind import Kind

READERS = {
    "cat", "head", "tail", "less", "more", "bat", "sed", "awk", "grep", "rg", "jq", "wc", "diff",
    "cmp", "nl", "cut", "sort", "uniq", "xxd", "od", "strings", "file", "stat", "python3", "node",
}
SEPARATORS = {"|", "||", "&&", ";", "&", "\n"}
WRITE_REDIRECTS = {">", ">>", ">|", "1>", "2>", "&>", "1>>", "2>>", "&>>"}   # the next word is written, not read
VIA_BASH = "via bash"


def bash_read_events(ctx: HookContext, command: str) -> list[Event]:
    base, seen, events = ctx.cwd, set(), []
    for words in _simple_commands(command):
        if words[0] == "cd" and len(words) > 1:
            base = _resolve(base, words[1])
            continue
        if os.path.basename(words[0]) not in READERS:
            continue
        args = words[1:]
        for index, arg in enumerate(args):
            if arg in WRITE_REDIRECTS or arg.startswith("-") or arg in seen or arg == "<":
                continue
            if index and args[index - 1] in WRITE_REDIRECTS:
                continue
            path = _resolve(base, arg)
            if os.path.isfile(path):
                seen.add(arg)
                events.append(ctx.event(Kind.READ, path, VIA_BASH))
    return events


def _simple_commands(command: str) -> list[list[str]]:
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=";&|<>")
    lexer.whitespace_split = True
    commands, current = [], []
    try:
        for token in lexer:
            if token in SEPARATORS or (set(token) <= set(";&|") and token):
                if current:
                    commands.append(current)
                current = []
            elif not current and "=" in token and not token.startswith("="):
                continue    # leading VAR=value assignment
            else:
                current.append(token)
    except ValueError:      # unbalanced quotes: give up on inference, the INVOKE line still shows the command
        return []
    if current:
        commands.append(current)
    return commands


def _resolve(base: str, path: str) -> str:
    path = os.path.expanduser(path)
    return os.path.normpath(path if os.path.isabs(path) else os.path.join(base, path))
