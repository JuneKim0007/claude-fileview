"""Full-width ═══[ text ]═══ banners, sized to the width at the moment they are drawn. frame() is the
geometry both the header banner and announce banners use; each caller colours the parts itself."""
from fileview.render.paths import elide_middle

FILL = "═"


def text_room(width: int) -> int:
    return max(8, width - 10)


def frame(text_width: int, width: int) -> tuple[str, str]:
    left = max(3, (width - text_width - 4) // 2)
    right = max(3, width - text_width - 4 - left)
    return FILL * left + "[ ", " ]" + FILL * right


def banner(title: str, width: int) -> str:
    shown = elide_middle(title, text_room(width))
    left, right = frame(len(shown), width)
    return left + shown + right
