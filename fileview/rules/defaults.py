"""Built-in rules: the source default.yaml is generated from, and the last resort when no config file
can be read. The git push captures and banners double as a worked example of capture + announce."""
from fileview.rules.model import CaptureRule, Match, PaletteSpec, PatternSet, Prefix, Rules, TextRule

DEFAULT_RULES = Rules(
    palette=PaletteSpec(
        kinds={"READ": "green", "WRITE": "blue", "CREATE": "yellow", "DELETE": "red", "INVOKE": "orange",
               "DONE": "grey", "FAILED": "red", "SEARCH": "cyan", "LOAD": "grey"},
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
    captures=(
        # "   1a2b3c4..5d6e7f8  main -> main"  (git reports pushes on stderr)
        CaptureRule("push", r"(^|[;&|]\s*)git push\b",
                    r"(?P<old>[0-9a-f]{7,40})\.\.(?P<new>[0-9a-f]{7,40})\s+(?P<branch>\S+)\s+->"),
        # " * [new branch]      feature -> feature"
        CaptureRule("pushnew", r"(^|[;&|]\s*)git push\b", r"\*\s+\[new branch\]\s+(?P<branch>\S+)\s+->"),
    ),
    announce=(
        TextRule(Match(kinds=("DONE",), command=r"\bgit push\b"),
                 "<yellow>git pushed</> {push.branch}  {push.old}..{push.new}"),
        TextRule(Match(kinds=("DONE",), command=r"\bgit push\b"), "<yellow>git pushed new branch</> {pushnew.branch}"),
        TextRule(Match(kinds=("FAILED",), command=r"\bgit push\b"), "<red>git push failed</>"),
    ),
    display=(),
)
