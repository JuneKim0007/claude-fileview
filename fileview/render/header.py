"""The block printed on open, reload and title change (banner, legend, rules source, config problems),
and the banner alone, which is all a resize reprints."""
from dataclasses import dataclass, field

from fileview.model.kind import Kind
from fileview.render.banner import banner
from fileview.render.palette import Palette


@dataclass(frozen=True)
class HeaderStatus:
    """Where the rules came from and what went wrong loading them, as the header shows it."""
    source: str
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def title_banner(title: str | None, session: str, width: int, palette: Palette) -> str:
    name = f"{title}  ·  {session}" if title else f"session {session}"
    return palette.bold(banner(name, width))


def header(title: str | None, session: str, width: int, palette: Palette, status: HeaderStatus) -> str:
    lines = ["", title_banner(title, session, width, palette),
             " ".join(palette.kind(kind, f"[{kind.value}]") for kind in Kind),
             palette.dim(f"rules {status.source}")]
    lines += [palette.colour("yellow", f"config: {problem}") for problem in status.problems]
    lines += [palette.dim(f"config: {note}") for note in status.notes]
    return "\n".join(lines)
