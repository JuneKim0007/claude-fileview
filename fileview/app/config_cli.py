"""`fileview config path | check [--json] | init [--force] | reset-default`. check's --json output is
the shape an MCP tool will return; its exit status is 1 when the rules a viewer would load have problems."""
import json

from fileview.config import config_file, lookup
from fileview.config.load import load_rules
from fileview.locations import DEFAULT_CONFIG, USER_CONFIG
from fileview.rules.defaults import DEFAULT_RULES


def run(args) -> int:
    command = args.config_command
    if command == "path":
        choice = lookup.choose()
        print(f"reads    {choice.path}  ({choice.origin}{'' if choice.path.is_file() else ', missing'})")
        print(f"fallback {DEFAULT_CONFIG}")
        print(f"order    --config, ${lookup.ENV_VARIABLE}, {USER_CONFIG}")
        return 0
    if command == "check":
        loaded = load_rules(args.config, confirm=None)
        if args.json:
            print(json.dumps(loaded.as_dict(), indent=2))
        else:
            print(f"rules from {loaded.source}")
            for problem in loaded.problems:
                print(f"problem: {problem}")
            for note in loaded.notes:
                print(f"note:    {note}")
            if not loaded.problems:
                print("ok")
        return 1 if loaded.problems else 0
    if command == "init":
        if USER_CONFIG.is_file() and not args.force:
            print(f"{USER_CONFIG} exists; use --force to back it up and replace it")
            return 1
        if USER_CONFIG.is_file():
            print(f"backed up to {config_file.backup(USER_CONFIG)}")
        print(f"wrote {config_file.write(USER_CONFIG, DEFAULT_RULES)}")
        return 0
    if command == "reset-default":
        print(f"wrote {config_file.write(DEFAULT_CONFIG, DEFAULT_RULES)}")
        return 0
    return 2
