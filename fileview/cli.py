"""Command line: `fileview <command> [session]`. Viewer commands go through the supervisor (which starts
on first use and stays up); `kill` deliberately does not, so it works when the supervisor is broken.
Imports are deferred into each handler so the hook path loads only what it uses."""
import argparse
import json
import os
import sys
import time


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fileview", description="Live view of the files Claude touches.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in [
        ("open", "open this session's viewer"), ("close", "close this session's viewer"),
        ("restart", "restart the viewer in place (or open it)"), ("reload", "re-read the rules file"),
        ("status", "is this session's viewer open"),
    ]:
        sub = commands.add_parser(name, help=text)
        sub.add_argument("session", nargs="?")
        if name in ("open", "restart"):
            sub.add_argument("--config", help="rules file to use instead of the lookup order")
    commands.add_parser("list", help="sessions the supervisor manages")
    commands.add_parser("kill", help="stop the supervisor and every viewer, without needing the supervisor")
    view = commands.add_parser("view", help="run the viewer here (the supervisor launches this)")
    view.add_argument("session")
    view.add_argument("--config")
    view.add_argument("--state", help="state directory of the supervisor that launched it")
    supervisor = commands.add_parser("supervisor", help="the control process").add_subparsers(dest="supervisor_command", required=True)
    supervisor.add_parser("run", help="run the supervisor in the foreground")
    supervisor.add_parser("status", help="is it up, which code, how long")
    supervisor.add_parser("stop", help="stop it; its viewers exit with it")
    config = commands.add_parser("config", help="the rules file").add_subparsers(dest="config_command", required=True)
    config.add_parser("path", help="which file a viewer would read, and the lookup order")
    check = config.add_parser("check", help="validate the rules a viewer would load")
    check.add_argument("--json", action="store_true", help="machine-readable result")
    check.add_argument("--config")
    init = config.add_parser("init", help="create the user rules file from the defaults")
    init.add_argument("--force", action="store_true", help="back up and replace an existing file")
    config.add_parser("reset-default", help="regenerate the shipped default file")
    for name in ("hook", "hook-start", "hook-end"):
        commands.add_parser(name, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.command == "hook":
        from fileview.capture.hook_entry import run
        return run()
    if args.command in ("hook-start", "hook-end"):
        return _session_hook(args.command)
    if args.command == "view":
        if args.state:              # before any fileview module computes its locations
            os.environ["CLAUDE_FILEVIEW_STATE"] = args.state
        return _view(args.session, args.config)
    if args.command == "config":
        from fileview import config_cli
        return config_cli.run(args)
    if args.command == "kill":
        from fileview.lifecycle import control
        print(control.kill_all())
        return 0
    if args.command == "supervisor":
        return _supervisor(args.supervisor_command)
    if args.command == "list":
        return _call("list", render=_render_list)

    session = (args.session or os.environ.get("CLAUDE_CODE_SESSION_ID", ""))[:8]
    if not session:
        print("fileview: no session id (outside Claude, pass one: fileview open <session>)", file=sys.stderr)
        return 1
    fields = {"session": session}
    if args.command in ("open", "restart"):
        from fileview.lifecycle.launchers.detect import terminal_hints
        fields.update(config=_absolute(args.config), env=terminal_hints(),
                      claude_pid=int(os.environ.get("CLAUDE_PID") or 0))
    if args.command == "status":
        return _call("status", render=lambda r: f"{r['session']}: {'open' if r['open'] else 'closed'}"
                     f" (attached={r['attached']}, wanted={r['wanted']})", **fields)
    return _call(args.command, **fields)


def _call(op: str, render=None, **fields) -> int:
    from fileview.supervisor.client import SupervisorUnavailable, call
    try:
        response = call(op, **fields)
    except SupervisorUnavailable as failure:
        print(f"fileview: supervisor unavailable, nothing done: {failure}", file=sys.stderr)
        return 1
    if not response.get("ok"):
        print(f"fileview: {response.get('error')}", file=sys.stderr)
        return 1
    print(render(response) if render else f"fileview: {response.get('message', 'ok')}")
    return 0


def _render_list(response: dict) -> str:
    rows = [f"{s['session']}  {'open' if s['open'] else 'closed':6} attached={s['attached']!s:5} "
            f"wanted={s['wanted']!s:5} claude_pid={s['claude_pid']}" for s in response["sessions"]]
    return "\n".join(rows) or "no sessions"


def _supervisor(command: str) -> int:
    if command == "run":
        from fileview.supervisor.server import serve
        return serve()
    if command == "stop":
        from fileview.lifecycle.control import stop_supervisor
        print(f"fileview: supervisor {stop_supervisor()}")
        return 0
    from fileview.supervisor.client import SupervisorUnavailable, call
    try:
        r = call("ping", start=False)
    except SupervisorUnavailable as failure:
        print(f"fileview: supervisor down ({failure})")
        return 1
    print(f"fileview: supervisor up, pid {r['pid']}, code {r['version']}, uptime {r['uptime']}s")
    return 0


def _session_hook(command: str) -> int:
    """Never fails the session; a failure is recorded in the state directory instead."""
    try:
        session_id = json.load(sys.stdin).get("session_id") or ""
        if not session_id:
            return 0
        from fileview.supervisor.client import call
        if command == "hook-end":
            call("close", session=session_id[:8], start=False)
            return 0
        from fileview.lifecycle.interactive import is_interactive
        from fileview.lifecycle.launchers.detect import terminal_hints
        if os.environ.get("CLAUDE_FILEVIEW_NO_VIEWER") or not is_interactive():
            return 0
        call("ensure", session=session_id[:8], env=terminal_hints(), claude_pid=int(os.environ.get("CLAUDE_PID") or 0))
    except Exception as failure:   # noqa: BLE001 - a session hook must never disturb the session
        _record_hook_failure(command, failure)
    return 0


def _record_hook_failure(command: str, failure: Exception) -> None:
    try:
        from fileview.locations import STATE_DIR
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_DIR / "hook-errors.log", "a") as log:
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {command}: {failure!r}\n")
    except OSError:
        pass


def _view(session: str, config: str | None) -> int:
    from fileview import viewer_app
    from fileview.lifecycle import registry
    registry.record(session)
    try:
        return viewer_app.run(session, config)
    except KeyboardInterrupt:
        return 0
    finally:
        registry.forget(session)


def _absolute(path: str | None) -> str | None:
    return os.path.abspath(os.path.expanduser(path)) if path else None
