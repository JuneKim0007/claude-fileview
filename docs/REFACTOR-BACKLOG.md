# Refactor backlog

Surveyed 2026-10-07 · scope `fileview/` (package, tests as proof) · 92 files
Baseline: tests 128 green · 3148 lines · 105 comment lines
History: 1 git commit + 135 edits in 6 change sets from fileview's own event log (thin history)

Order: deletions, then dependencies, then technique phase order (composing → moving → organizing).

## Open

### R1 · Dead code · fileview/control/confirm.py:17 · never_confirm
status   planned
evidence grep -rnw 'never_confirm' over repo (.py .md .yaml .json, tests, bin): 1 hit, the definition
remedy   delete (no edges to unlink) -> how-to-refactor
expect   -4 lines; re-grep returns nothing; tests green
blocked  none
safety   SAFE
first seen 2026-10-07

### R2 · Dead code · fileview/lifecycle/registry.py:71 · recorded_sessions
status   planned
evidence grep -rnw 'recorded_sessions': 1 hit, the definition; its caller list_viewers was removed with the supervisor
remedy   delete -> how-to-refactor
expect   -2 lines; cascade checked: VIEWERS_DIR.glob still used by forget_all
blocked  none
safety   SAFE
first seen 2026-10-07

### R3 · Comments · fileview/rules/model.py · Match/PatternSet/Rules field comments
status   planned
evidence 28% comment lines (20/70); 4 restate the override order owned by rules/pipeline.py
remedy   delete the 4 restating lines; keep facts the code does not state -> how-to-refactor
expect   -4 comment lines
blocked  none
safety   SAFE
first seen 2026-10-07

### R4 · Duplicate code · fileview/render/line.py:33 · command-kind predicate; ELLIPSIS
status   planned
evidence (INVOKE, DONE, FAILED) spelled in render/line.py:33 and rules/pipeline.py:22; ELLIPSIS in render/paths.py:4 and render/template_text.py:6
remedy   Extract Variable / import the single definition -> refactor-composing-method
expect   -2 lines; one definition each
blocked  none
safety   SAFE
first seen 2026-10-07

### R5 · Duplicate code · fileview/render/banner.py:banner + fileview/render/line.py:_banner
status   planned
evidence two full-width banner builders (plain title vs template parts); FILL defined in both
remedy   Substitute Algorithm: one banner(inner, visible_len, width) -> refactor-composing-method
expect   -8 lines; one algorithm; Banner tests + git-push banner test unchanged
blocked  none
safety   SAFE
first seen 2026-10-07

### R6 · Long method · fileview/supervisor/reconcile.py:30 · reconcile
status   planned
evidence nesting 6 (threshold 4); two independent passes (running viewers / wanted sessions) in one body
remedy   Extract Method: _sweep_running, _review_wanted -> refactor-composing-method
expect   nesting 6 -> 3; 5 reconcile unit tests unchanged
blocked  none
safety   SAFE
first seen 2026-10-07

### R7 · Feature envy · fileview/supervisor/state.py · SupervisorState (callers: reconcile.py, handlers.py, server.py)
status   planned
evidence 7 direct reads/writes of state.attached / state.last_seen outside state.py; grace test computed 2x; `entry.env if entry else None` 3x in handlers
remedy   Move Method: SupervisorState.is_attached / seen / stale; SessionTable.env_of -> refactor-moving-feats-btw-objects
expect   0 outside accesses to the dicts; one grace computation
blocked  R6 (do after, the passes are where the reads live)
safety   SAFE (new methods run under the state.lock callers already hold)
first seen 2026-10-07

### R8 · Data clump + feature envy · fileview/config/load.py:55,73 · _read_or_repair / _default_rules
status   planned
evidence (config_file, result, confirm) passed together through both; config_file is a module passed as an argument; LoadedRules mutated from outside 10x
remedy   Replace Method with Method Object: RulesLoader(config_file, confirm) owning the result -> refactor-composing-method
expect   no module-as-argument; 10 test_load cases unchanged
blocked  none
safety   SAFE
first seen 2026-10-07

### R9 · Divergent change · fileview/supervisor/server.py:60 · serve   (thin history)
status   planned
evidence 15 edits in 3 change sets for 3 reasons (link protocol, process lifecycle, background loop); shutdown vs handover teardown inline in `finally`
remedy   Extract Method: _teardown(state, handing_over) only; no new module (thin history does not justify more) -> refactor-composing-method
expect   serve 40 -> ~28 lines; 6 integration tests unchanged
blocked  none
safety   SAFE (smaller change)
first seen 2026-10-07

### R10 · Primitive obsession · session id prefix · app/cli.py, supervisor/server.py, supervisor/handlers.py
status   planned
evidence `[:8]` at 5 sites in 3 files
remedy   one short_session(id) function (not a value object: the prefix is in stored records and the protocol) -> refactor-organizing-data
expect   the prefix length defined once
blocked  none
safety   RECONSIDER for a value object; SAFE for the function
first seen 2026-10-07

### R11 · Refused bequest · fileview/lifecycle/launchers/{iterm,tmux}.py · close_idle_windows
status   planned
evidence 2 of 3 Launcher implementations are `pass`; the opt-out is not stated in base.py
remedy   document the opt-out in the Launcher protocol (panes that close themselves) -> how-to-refactor
expect   docstring only; no behaviour change
blocked  none
safety   SAFE
first seen 2026-10-07

### R12 · Duplicate code · fileview/config/config_file.py:37 + fileview/config/captures_export.py:24 · atomic write
status   blocked
evidence same mkdir / <name>.partial / os.replace sequence; a 3rd copy in supervisor/session_table.py:62
remedy   Extract Method atomic_write inside config/ only -> refactor-composing-method
expect   -4 lines in config/
blocked  characterisation test for captures_export.export (0 direct tests)
safety   RECONSIDER until the test exists
principles traded DRY for axis independence: session_table keeps its own copy (supervisor must not import a config file-I/O helper)
first seen 2026-10-07

### R13 · Duplicate code · fileview/lifecycle/interactive.py:20 · _ps
status   blocked
evidence a second private ps wrapper; lifecycle/processes.py covers the need
remedy   Substitute Algorithm: use processes (add tty_of) -> refactor-composing-method
blocked  characterisation test for is_interactive (0 tests)
safety   RECONSIDER until the test exists
first seen 2026-10-07

### R14 · Long parameter list · fileview/render/header.py:13 · header
status   blocked
evidence 7 params; source/problems/notes are 3 fields of LoadedRules
remedy   Introduce Parameter Object, reshaped by principles: header(..., status_lines: list[str]) (passing LoadedRules would make render import config) -> refactor-simplifying-method
blocked  header test (0 tests)
safety   RECONSIDER until the test exists
first seen 2026-10-07

### R15 · Long method + divergent change · fileview/app/viewer.py:88 · run
status   blocked
evidence 42 statements, nesting 4; 19 edits across 3 change sets (reload, resize, handover)
remedy   Extract Method: the supervision/handover block -> refactor-composing-method
blocked  test for the extracted handover step (the viewer loop has 0 tests)
safety   RECONSIDER until the test exists
first seen 2026-10-07

### R16 · Switch statements · fileview/supervisor/handlers.py:13 · dispatch
status   blocked
evidence 12 if-branches on `op`; adding an op means editing this chain
remedy   Replace Conditional with an op -> handler table in handlers.py only -> refactor-simplifying-conditional-expressions
blocked  handler tests with mocked viewers for open/close/reload/restart (untested: they need a terminal)
safety   RECONSIDER until the tests exist
first seen 2026-10-07

## Done

## Dropped

### R17 · Long method · fileview/store/follower.py:13 · follow
dropped 2026-10-07 — nesting 5 vs threshold 4; a single-handle tail -F generator; splitting it costs `yield from` plumbing that outweighs one level

### R18 · Duplicate code · fileview/supervisor/client.py:request + fileview/supervisor/link.py:attach
dropped 2026-10-07 — the lifetimes differ on purpose (one-shot request vs persistent fail-closed link) and the error mapping differs; unifying saves ~5 lines and couples them

### R19 · Shotgun surgery · {rules/model, rules/defaults, rules/resolve, render/line}   (thin history)
dropped 2026-10-07 — the axis split is deliberate (vocabulary / data / evaluation / drawing); pipeline.py already holds the order in one place; revisit once git history exists

### R20 · bug, not a smell · fileview/app/viewer.py:_home_short
dropped 2026-10-07 — `startswith(home)` has no separator check ("/Users/nameX" -> "~X"), unlike rules/resolve.place. Fix as a bug; the dedupe with place() is then SAFE

## Refused

### R21 · Switch statements · fileview/app/cli.py:11 · main
refused — a router: mapping commands to requests is the file's job (the supervisor side is R16)
