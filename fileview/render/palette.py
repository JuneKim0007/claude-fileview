"""Colours resolved from the rules' palette into ANSI codes. Colour is off when output is not a
terminal or NO_COLOR is set; a colour the palette cannot resolve is drawn plain."""
import os
from dataclasses import dataclass

from fileview.model.kind import Kind
from fileview.rules.colours import sgr
from fileview.rules.model import Colour, PaletteSpec

RESET, DIM, BOLD = "\033[0m", "\033[2m", "\033[1m"


@dataclass(frozen=True)
class Palette:
    enabled: bool
    spec: PaletteSpec

    @classmethod
    def for_stream(cls, stream, spec: PaletteSpec) -> "Palette":
        return cls(enabled=stream.isatty() and "NO_COLOR" not in os.environ, spec=spec)

    def kind(self, kind: Kind, text: str) -> str:
        return self.colour(self.spec.kinds.get(kind.value, ""), text)

    def label(self, text: str, colour: Colour = "") -> str:
        return self.colour(colour if colour != "" else self.spec.label, text)

    def colour(self, colour: Colour, text: str) -> str:
        if colour == "":
            return text
        try:
            code = f"\033[{sgr(colour, self.spec.colours)}m"
        except ValueError:
            return text
        return self._wrap(code, text)

    def dim(self, text: str) -> str:
        return self._wrap(DIM, text)

    def bold(self, text: str) -> str:
        return self._wrap(BOLD, text)

    def _wrap(self, code: str, text: str) -> str:
        return f"{code}{text}{RESET}" if self.enabled and text else text
