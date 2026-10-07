"""A colour value -> the ANSI SGR parameters that draw it. Raises ValueError for anything unknown,
so a config can be rejected before it reaches the screen."""
import re

from fileview.rules.model import Colour

BUILT_IN = {
    "black": "30", "red": "31", "green": "32", "yellow": "33", "blue": "34", "magenta": "35",
    "cyan": "36", "white": "37", "grey": "90", "gray": "90", "orange": "38;5;208", "purple": "38;5;141",
}
HEX = re.compile(r"#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})")


def sgr(colour: Colour, custom: dict[str, Colour] | None = None) -> str:
    if isinstance(colour, str) and custom and colour in custom:
        colour = custom[colour]              # one level: a custom name points at a concrete colour
    if isinstance(colour, bool):
        raise ValueError(f"unknown colour {colour!r}")
    if isinstance(colour, int):
        if 0 <= colour <= 255:
            return f"38;5;{colour}"
        raise ValueError(f"colour index {colour} outside 0-255")
    if colour in BUILT_IN:
        return BUILT_IN[colour]
    match = HEX.fullmatch(colour)
    if match:
        return "38;2;" + ";".join(str(int(part, 16)) for part in match.groups())
    raise ValueError(f"unknown colour {colour!r}; use a name ({', '.join(sorted(BUILT_IN))}), a custom name, #rrggbb or 0-255")
