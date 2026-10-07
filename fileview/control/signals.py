"""Which signal requests which action. Shared by the receiver (the viewer installs handlers) and the
sender (lifecycle looks up the signal for an action), so the two can never disagree."""
import signal

from fileview.control.actions import ActionRegistry

SIGNAL_FOR_ACTION = {
    "reload": signal.SIGHUP,      # re-read the rules file (nginx, sshd and most daemons use HUP this way)
    "restart": signal.SIGUSR1,    # re-exec the viewer process in place
    "redraw": signal.SIGWINCH,    # the terminal sends this itself on resize
}


def install(registry: ActionRegistry) -> None:
    for action, signum in SIGNAL_FOR_ACTION.items():
        signal.signal(signum, lambda _signum, _frame, name=action: registry.request(name))
