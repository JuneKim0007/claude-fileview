"""The block printed at the top and after a redraw: banner, legend, the rules source, and any config
problems with how to fix them."""
from fileview.model.kind import Kind
from fileview.render.banner import banner
from fileview.render.palette import Palette


def header(title: str | None, session: str, width: int, palette: Palette,
           source: str, problems: list[str], notes: list[str]) -> str:
    name = f"{title}  ·  {session}" if title else f"session {session}"
    lines = ["", palette.bold(banner(name, width)),
             " ".join(palette.kind(kind, f"[{kind.value}]") for kind in Kind),
             palette.dim(f"rules {source}")]
    lines += [palette.colour("yellow", f"config: {problem}") for problem in problems]
    lines += [palette.dim(f"config: {note}") for note in notes]
    return "\n".join(lines)
