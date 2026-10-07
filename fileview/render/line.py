"""One event -> one line: `[KIND]   [label] path  detail  <agent>`, fitted to the width; None when
the rules hide the event's path. Events without a path (commands, overflow notes) are always shown."""
from fileview.model.event import Event
from fileview.model.kind import Kind
from fileview.render.palette import Palette
from fileview.render.paths import elide_middle
from fileview.rules.model import Rules
from fileview.rules.resolve import resolve

TAG_WIDTH = 9                          # "[CREATE] " is the widest tag


def format_line(event: Event, root: str, width: int, palette: Palette, rules: Rules) -> str | None:
    tag = palette.kind(event.kind, f"[{event.kind.value}]".ljust(TAG_WIDTH))
    agent = "" if event.agent == "main" else f"  <{event.agent}>"
    room = max(10, width - TAG_WIDTH - len(agent) - 1)
    if event.kind is Kind.INVOKE:
        return tag + elide_middle("$ " + " ; ".join(event.detail.splitlines()), room) + palette.dim(agent)
    detail = f"  {event.detail}" if event.detail else ""
    if not event.path:
        return tag + palette.dim(detail.strip()[:room] + agent)
    view = resolve(event.path, root, rules)
    if not view.visible:
        return None
    label = f"[{view.label}] " if view.label else ""
    path = elide_middle(view.rest, max(10, room - len(label) - len(detail)))
    return (tag + palette.label(label, view.label_colour) + palette.colour(view.colour, path)
            + palette.dim(detail[: max(0, room - len(label) - len(path))] + agent))
