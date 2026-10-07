"""A full-width ═══[ title ]═══ banner, sized to the width at the moment it is drawn."""
from fileview.render.paths import elide_middle

FILL = "═"


def banner(title: str, width: int) -> str:
    label = f"[ {elide_middle(title, max(8, width - 10))} ]"
    left = max(3, (width - len(label)) // 2)
    right = max(3, width - len(label) - left)
    return FILL * left + label + FILL * right
