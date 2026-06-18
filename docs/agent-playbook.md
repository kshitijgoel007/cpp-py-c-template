# Agent Playbook

## Mandatory Environment Policy

- `sudo` is prohibited for every build, install, test, and cleanup operation.
- All installation prefixes must be writable by the current user.
- Every Python command must run in an environment created by `virtualenv`.
- Use `just env` for the repository `.venv`; do not use stdlib `venv` or
  system-level Python package installation.

## Architecture

The project has one implementation and two adapters:

```text
                       +-------------------+
                       |   c_lib/c_lib.c   |
                       | implementation +  |
                       | stable C ABI      |
                       +---------+---------+
                                 |
                    +------------+------------+
                    |                         |
          +---------v---------+     +---------v----------+
          | cpp_wrapper/      |     | generated _ctypes  |
          | C++17 adapter     |     | ctypes ABI adapter |
          +---------+---------+     +---------+----------+
                    |                         |
               C++ users            wrapper.py / Python users
```

The C header is the integration seam. A change that compiles in one wrapper
can still break the other wrapper or the packaged native library, so public
API work is validated as a vertical slice.

The complete Python binding and wheel design is documented in
`docs/python-bindings.md`.

## Change Recipes

### Add a Function

1. Declare it in `c_lib/c_lib.h` with a complete contract.
2. Implement it in `c_lib/c_lib.c`.
3. Expose an idiomatic operation in `cpp_wrapper/`.
4. Regenerate API metadata and ctypes bindings.
5. Add a typed function in `wrapper.py` and export it from `__init__.py`.
6. Add or update consumer-level coverage for both languages.
7. Build and run both smoke tests.

### Change a C Type or Signature

Assume the change is ABI-breaking until proven otherwise. Search all call
sites, regenerate bindings, and check C/C++ conversions plus Python range and
ownership behavior. Prefer adding a new symbol and deprecating the old symbol
when compatibility matters.

### Add an Opaque Resource

Expose an incomplete C struct and explicit create/destroy functions. Wrap it
with RAII in C++ and a deterministic close/context-manager API in Python.
Specify whether null is accepted and how allocation failures are reported.
Use the starter `CAccumulator`/`Accumulator` implementation and its lifecycle
tests as the reference pattern.

### Change Native Packaging

Account for Linux (`.so`), macOS (`.dylib`), and Windows (`.dll`). Verify the
built wheel contains the native library and test import from outside the
repository so source-tree files cannot mask a packaging defect.

## Efficient Investigation

Use repository-wide search before edits:

```bash
rg "symbol_name|public_name"
rg --files
git status --short
```

Read only the relevant generated bindings when debugging; generated output is
evidence, not a patch target.

## Review Priorities

Review cross-language changes in this order:

1. Memory safety and ownership.
2. ABI compatibility and exact type widths.
3. Error propagation across boundaries.
4. Native-library discovery and packaging.
5. Public API consistency and documentation.
6. Style and local cleanup.
