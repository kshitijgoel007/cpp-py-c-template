# CLAUDE.md

`AGENTS.md` and the nested `AGENTS.md` files in each directory are the
authoritative instructions for this repository. Read the nearest one before
touching any file.

## Fast-path rules

- No `sudo`.
- All Python in `.venv` created by `virtualenv`. Run `just env` first.
- Never edit `src/my_c_wrapper/_ctypes.py` — regenerate with `just bindings`.
- A public C change is not done until C++, Python, and tests are updated.
- Run `just check` before marking any task complete.

## Claude Code session continuity

Persistent memory lives in `.claude/` (auto-managed by Claude Code). Save user
preferences and surprising non-obvious decisions there. Architecture, rules,
and commands belong in `AGENTS.md`, not in memory.
