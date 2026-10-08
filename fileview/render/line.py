"""One event's Plan -> the lines to print: its banners first (═══[ text ]═══), then its own line
`[KIND]   [label] path  detail  <agent>` or the display template's body. Everything is fitted to the
width here, the last layer of the pipeline."""
from fileview.model.event import Event
from fileview.render.banner import frame, text_room
from fileview.render.palette import Palette
from fileview.render.paths import elide_middle
from fileview.render.template_text import draw, visible_length
from fileview.rules.model import Rules
from fileview.rules.pipeline import COMMAND_KINDS, plan
from fileview.rules.template import Part

TAG_WIDTH = 9                          # "[CREATE] " is the widest tag


def format_event(event: Event, root: str, width: int, palette: Palette, rules: Rules) -> list[str]:
    planned = plan(event, rules, root)
    if planned is None:
        return []
    lines = [_banner(parts, width, palette) for parts in planned.banners]
    if planned.show_line:
        lines.append(_line(event, planned, width, palette))
    return lines


def _line(event: Event, planned, width: int, palette: Palette) -> str:
    tag = palette.kind(event.kind, f"[{event.kind.value}]".ljust(TAG_WIDTH))
    agent = "" if event.agent == "main" else f"  <{event.agent}>"
    room = max(10, width - TAG_WIDTH - len(agent) - 1)
    if planned.body is not None:
        return tag + draw(planned.body, palette, room) + palette.dim(agent)
    if event.kind in COMMAND_KINDS:
        return tag + elide_middle("$ " + " ; ".join(event.detail.splitlines()), room) + palette.dim(agent)
    detail = f"  {event.detail}" if event.detail else ""
    if planned.placement is None:
        return tag + palette.dim(detail.strip()[:room] + agent)
    place = planned.placement
    label = f"[{place.label}] " if place.label else ""
    path = elide_middle(place.rest, max(10, room - len(label) - len(detail)))
    return (tag + palette.label(label, place.label_colour) + palette.colour(planned.path_colour, path)
            + palette.dim(detail[: max(0, room - len(label) - len(path))] + agent))


def _banner(parts: tuple[Part, ...], width: int, palette: Palette) -> str:
    room = text_room(width)
    left, right = frame(min(visible_length(parts), room), width)
    return palette.dim(left) + draw(parts, palette, room) + palette.dim(right)
