"""Built-in rules: the source default.yaml is generated from, and the last resort when no config
file can be read. Longest prefix wins; the session's project root beats every prefix."""
from fileview.rules.model import PaletteSpec, PatternSet, Prefix, Rules

DEFAULT_RULES = Rules(
    palette=PaletteSpec(
        kinds={"READ": "green", "WRITE": "blue", "CREATE": "yellow", "DELETE": "red",
               "INVOKE": "orange", "SEARCH": "cyan", "LOAD": "grey"},
        label="magenta",
        colours={},
    ),
    prefixes=(
        Prefix("~/.claude/fileview", "fileview"),
        Prefix("~/.claude/projects", "claude-transcripts"),
        Prefix("~/.claude/commands", "claude-commands"),
        Prefix("~/.claude/skills", "claude-skills"),
        Prefix("~/.claude/plugins", "claude-plugins"),
        Prefix("~/.claude/hooks", "claude-hook"),
        Prefix("~/.claude", "claude"),
        Prefix("~/.config/claude-fileview", "fileview-config"),
        Prefix("/private/tmp", "tmp"),
        Prefix("/tmp", "tmp"),
        Prefix("/private/var/folders", "tmp"),
        Prefix("/var/folders", "tmp"),
    ),
    ignore=PatternSet(),
    deignore=PatternSet(),
    colour=(),
)
