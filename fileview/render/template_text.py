"""Filled template parts -> terminal text that fits a width. Width is counted on visible characters
only, so colour codes never cause early truncation."""
from fileview.render.palette import Palette
from fileview.render.paths import ELLIPSIS
from fileview.rules.template import Part


def visible_length(parts: tuple[Part, ...]) -> int:
    return sum(len(p.data) for p in parts if p.kind == "text")


def draw(parts: tuple[Part, ...], palette: Palette, max_width: int, base_colour="") -> str:
    out, colour, used = [], base_colour, 0
    budget = max_width if visible_length(parts) <= max_width else max_width - len(ELLIPSIS)
    for part in parts:
        if part.kind == "colour":
            colour = part.data
        elif part.kind == "reset":
            colour = base_colour
        elif part.kind == "text" and used < budget:
            piece = part.data[: budget - used]
            used += len(piece)
            out.append(palette.colour(colour, piece) if colour != "" else piece)
    if budget < max_width:
        out.append(ELLIPSIS)
    return "".join(out)
