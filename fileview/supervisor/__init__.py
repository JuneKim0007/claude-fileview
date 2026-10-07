"""supervisor axis: the per-user control plane. One long-running process owns which viewers exist;
viewers stay independent processes that read the log themselves, and exit when the supervisor does."""
