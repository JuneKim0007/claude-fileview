"""The block printed on open, reload and title change (banner, legend, rules source, config problems),
and the banner alone, which is all a resize reprints."""
from fileview.model.kind import Kind
from fileview.render.banner import banner
from fileview.render.palette import Palette


def title_banner(title: str | None, session: str, width: int, palette: Palette) -> str:
    name = f"{title}  ·  {session}" if title else f"session {session}"
    return palette.bold(banner(name, width))


def header(title: str | None, session: str, width: int, palette: Palette,
           source: str, problems: list[str], notes: list[str]) -> str:
    lines = ["", title_banner(title, session, width, palette),
             " ".join(palette.kind(kind, f"[{kind.value}]") for kind in Kind),
             palette.dim(f"rules {source}")]
    lines += [palette.colour("yellow", f"config: {problem}") for problem in problems]
    lines += [palette.dim(f"config: {note}") for note in notes]
    return "\n".join(lines)
