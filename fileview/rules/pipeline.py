"""THE override order (z-order). One event in, one Plan out; every layer is here, in this order:

  1 ignore     first match hides   ─┐ visibility: deignore beats ignore regardless of list order;
  2 deignore   first match unhides ─┘ a still-hidden event stops here (no banner, no line)
  3 announce   EVERY match adds a banner line, in list order
  4 display    FIRST match replaces the line's body
  5 colour     FIRST match colours the path (ignored when a display template draws the body)
  6 place      longest prefix labels the path; the project root beats every prefix
  (7 fit to width happens in render, last)

A template rule fires only when every {placeholder} has a value. A DONE event (a finished command)
draws no line of its own unless a display rule gives it one; it exists to carry captured values."""
from dataclasses import dataclass

from fileview.model.event import Event
from fileview.model.kind import Kind
from fileview.rules.match import in_set, matches, path_matches
from fileview.rules.model import Colour, Rules
from fileview.rules.resolve import Placement, place
from fileview.rules.template import Part, parse

COMMAND_KINDS = (Kind.INVOKE, Kind.DONE, Kind.FAILED)


@dataclass(frozen=True)
class Plan:
    banners: tuple[tuple[Part, ...], ...]   # filled announce templates, in order
    body: tuple[Part, ...] | None           # filled display template, or None for the default body
    show_line: bool
    placement: Placement | None             # None when the event has no path
    path_colour: Colour


def plan(event: Event, rules: Rules, root: str) -> Plan | None:
    """None means hidden (layers 1-2)."""
    kind, path = event.kind.value, event.path
    command = event.detail if event.kind in COMMAND_KINDS else ""
    if in_set(rules.ignore, kind, command, path) and not in_set(rules.deignore, kind, command, path):
        return None
    placement = place(path, root, rules) if path else None
    values = {"command": command, "path": placement.text() if placement else "", "kind": kind,
              "agent": event.agent, "session": event.session, **event.values}
    banners = tuple(filled for rule in rules.announce
                    if matches(rule.match, kind, command, path)
                    and (filled := parse(rule.text).fill(values)) is not None)
    body = next((filled for rule in rules.display
                 if matches(rule.match, kind, command, path)
                 and (filled := parse(rule.text).fill(values)) is not None), None)
    colour = next((r.colour for r in rules.colour if path and path_matches(path, r.glob, r.regex)), "")
    return Plan(banners, body, body is not None or event.kind is not Kind.DONE, placement, colour)
