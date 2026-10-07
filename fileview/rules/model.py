"""The rule vocabulary. Visibility and colour are independent axes: ignore/deignore decide whether a
path is shown; colour rules decide how a shown path looks. A hidden path is never drawn."""
from dataclasses import dataclass, field

Colour = str | int     # built-in name, custom name, "#rrggbb", or 0-255


@dataclass(frozen=True)
class PatternSet:
    glob: tuple[str, ...] = ()       # fnmatch on the absolute path; "~" is expanded
    regex: tuple[str, ...] = ()      # re.search on the absolute path


@dataclass(frozen=True)
class ColourRule:
    colour: Colour
    glob: str = ""
    regex: str = ""


@dataclass(frozen=True)
class Prefix:
    path: str                        # absolute or ~-relative directory
    label: str                       # shown as [label] in place of the directory
    colour: Colour = ""              # highlight for this label; "" uses the palette's label colour


@dataclass(frozen=True)
class PaletteSpec:
    kinds: dict[str, Colour] = field(default_factory=dict)      # Kind name -> colour
    label: Colour = "magenta"
    colours: dict[str, Colour] = field(default_factory=dict)    # custom names -> colour


@dataclass(frozen=True)
class Rules:
    palette: PaletteSpec = field(default_factory=PaletteSpec)
    prefixes: tuple[Prefix, ...] = ()
    ignore: PatternSet = field(default_factory=PatternSet)      # hide when matched...
    deignore: PatternSet = field(default_factory=PatternSet)    # ...unless matched here
    colour: tuple[ColourRule, ...] = ()                         # first match wins
