"""The rule vocabulary. The order the rules apply in (the z-order) lives in rules/pipeline.py; this file
only says what each rule is. Visibility and colour are independent: a hidden event is never drawn."""
from dataclasses import dataclass, field

Colour = str | int     # built-in name, custom name, "#rrggbb", or 0-255


@dataclass(frozen=True)
class Match:
    """Selects events; every given field must hold, an empty Match selects everything."""
    kinds: tuple[str, ...] = ()      # any of these Kind names
    command: str = ""                # re.search on the command (INVOKE / DONE / FAILED)
    glob: str = ""                   # fnmatch on the absolute path; "~" is expanded
    regex: str = ""                  # re.search on the absolute path


@dataclass(frozen=True)
class PatternSet:
    glob: tuple[str, ...] = ()       # shorthand: path globs
    regex: tuple[str, ...] = ()      # shorthand: path regexes
    match: tuple[Match, ...] = ()    # full matches (kind / command / path)


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
class CaptureRule:
    """Named groups to keep from a finished command; compiled into captures.json for the hook."""
    name: str
    command: str                     # regex on the command; its named groups are captured too
    output: str = ""                 # regex on stdout+stderr; when given it must match


@dataclass(frozen=True)
class TextRule:
    """A template ("<red>pushed</> {push.new}") drawn for matching events: as a banner (announce)
    or in place of the line's body (display). Fires only when every placeholder has a value."""
    match: Match
    text: str


@dataclass(frozen=True)
class PaletteSpec:
    kinds: dict[str, Colour] = field(default_factory=dict)      # Kind name -> colour
    label: Colour = "magenta"
    colours: dict[str, Colour] = field(default_factory=dict)    # custom names -> colour


@dataclass(frozen=True)
class Rules:
    palette: PaletteSpec = field(default_factory=PaletteSpec)
    prefixes: tuple[Prefix, ...] = ()
    ignore: PatternSet = field(default_factory=PatternSet)
    deignore: PatternSet = field(default_factory=PatternSet)
    colour: tuple[ColourRule, ...] = ()
    captures: tuple[CaptureRule, ...] = ()
    announce: tuple[TextRule, ...] = ()
    display: tuple[TextRule, ...] = ()
