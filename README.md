# C Core with C++ and Python Layers

A template for implementing functionality once in C and exposing it through
independent C++17 and Python APIs.

```text
              c_lib/c_lib.c — implementation + stable C ABI
                       /                   \
            cpp_wrapper/              generated ctypes
               C++ API                       |
                                       Python wrapper
```

`c_lib/` owns implementation and the foreign-function interface. `cpp_wrapper/`
adds C++ ergonomics. `src/my_c_wrapper/` adds Python ergonomics. Neither
wrapper depends on the other.

The starter API covers two common binding shapes: `add()` is a stateless
function; `Accumulator` owns an opaque C allocation, uses RAII in C++, and
exposes a context manager in Python that translates C status codes into
exceptions.

## Prerequisites

- CMake 3.24 or newer
- A C11 and C++17 compiler
- Clang, used to extract the public C API from the header
- Python 3.11 or newer
- `virtualenv` — all Python work runs in environments it creates
- `just` — install with your package manager (`brew install just`, etc.)

Install `virtualenv` with an OS package manager or `pipx`. Do not install it
into the system interpreter.

## Environment policy

`sudo` is prohibited. Every Python command must run inside a `virtualenv`
environment. The package enforces this at import time.

Bootstrap once:

```bash
just env
```

This creates `.venv` and installs the Python dev tools inside it. All
`just` workflows that need Python depend on `env` automatically.

## Quick start

```bash
just check           # build, test, lint, ABI and policy validation
just wheel           # build a platform-tagged wheel under dist/
just package-smoke   # test clean editable and wheel installs
```

## Commands

| Command | Purpose |
| --- | --- |
| `just` | List available workflows |
| `just env` | Create `.venv` and install dev tools |
| `just build [preset]` | Configure and build a CMake preset (`dev`, `release`, `asan`, `coverage`) |
| `just bindings` | Extract C metadata and regenerate `_ctypes.py` |
| `just test` | Run CTest, pytest, and both consumer demos |
| `just check` | Full build, test, lint, ABI, and policy check |
| `just coverage` | Build with coverage and produce an XML report |
| `just sanitize` | Build and test with address and UB sanitizers |
| `just wheel` | Build a platform-tagged wheel under `dist/` |
| `just package-smoke [mode]` | Test clean installs: `all`, `editable`, or `wheel` |
| `just install-cpp [prefix]` | Install the C/C++ SDK under a user-writable prefix |
| `just clean` | Remove all generated artifacts |

## Repository layout

```text
.
├── bindings/bindings.toml       binding, ownership, ABI, and callback policy
├── c_lib/
│   ├── c_lib.h                  public C ABI (source of truth)
│   └── c_lib.c                  core implementation
├── cpp_wrapper/
│   ├── cpp_wrapper.h            public C++17 API
│   └── cpp_wrapper.cpp
├── src/my_c_wrapper/
│   ├── wrapper.py               handwritten Python API
│   ├── __init__.py              package exports
│   ├── _loader.py               native-library discovery
│   ├── _ctypes.py               generated — do not edit
│   └── lib/                     copied native library — do not commit
├── tools/
│   ├── bindings/                API extraction, code generation, ABI probe
│   └── native_build_backend/    PEP 517 backend for platform wheels
├── tests/
│   ├── c/test_c_api.c           C API tests (CTest)
│   ├── cpp/test_cpp_wrapper.cpp C++ tests (GoogleTest/CTest)
│   ├── python/test_wrapper.py   Python public-API tests (pytest)
│   └── consumer/                external find_package consumer test
├── docs/
│   ├── agent-playbook.md
│   ├── python-bindings.md
│   ├── abi-policy.md
│   └── file-map.md              purpose of every tracked file
├── CMakeLists.txt
├── CMakePresets.json
├── pyproject.toml
├── main.cpp                     C++ consumer demo
├── main.py                      Python consumer demo
└── justfile
```

## Binding pipeline

```text
c_lib/c_lib.h + bindings/bindings.toml
             |
        Clang JSON AST
             |
             v
   build/bindings/api.json          ← normalized C facts
             |
     ctypes code generator
             |
             v
  src/my_c_wrapper/_ctypes.py       ← generated, do not edit
             |
             v
  src/my_c_wrapper/wrapper.py       ← handwritten Python API
```

`bindings/bindings.toml` records decisions C syntax cannot express: which
symbols form the Python surface, ownership of returned pointers, array
pointer/count pairs, callback lifetimes, and records requiring ABI checks.
`just check` compiles a C probe to verify that generated `ctypes` sizes,
alignments, and field offsets match the compiler's view.

## Extending the template

For any new public operation, update the full vertical slice:

1. Declare it in `c_lib/c_lib.h`.
2. Implement it in `c_lib/c_lib.c`.
3. Add it to `bindings/bindings.toml` if it belongs in Python.
4. Expose an idiomatic C++ operation in `cpp_wrapper/`.
5. Expose a Python operation in `wrapper.py` and export from `__init__.py`.
6. Add tests in `tests/c/`, `tests/cpp/`, and `tests/python/`.
7. Run `just check`; run `just package-smoke` when packaging changes.

Prefer opaque C handles with explicit create/destroy for owned resources, RAII
in C++, and `close()`/context managers in Python.

## Agentic development

[`AGENTS.md`](AGENTS.md) and the nested `AGENTS.md` files in each directory
are the canonical instructions for any agent. They cover architecture, rules,
commands, and change recipes.

Tool-specific entry points defer to `AGENTS.md` rather than duplicating it:
[`CLAUDE.md`](CLAUDE.md) for Claude Code and
[`.github/copilot-instructions.md`](.github/copilot-instructions.md) for
GitHub Copilot. Add equivalent thin shims for other tools as needed.

See [`docs/agent-playbook.md`](docs/agent-playbook.md) for architecture
diagrams and [`docs/python-bindings.md`](docs/python-bindings.md) for the
binding design.
