# Copilot Instructions

`AGENTS.md` and the nested `AGENTS.md` files in each directory are the
authoritative instructions for this repository. Read the nearest one before
editing any file.

## Fast-path rules

- No `sudo`.
- All Python runs in `.venv` created by `virtualenv`. Run `just env` first.
- Never edit `src/my_c_wrapper/_ctypes.py` — regenerate with `just bindings`.
- A public C change is not done until C++, Python, and tests are updated.
- Run `just check` before marking any task complete.
