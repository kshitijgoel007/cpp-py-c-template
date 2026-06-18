# ABI and Versioning Policy

The project has three related compatibility surfaces:

1. The C ABI exported by `c_lib`.
2. The C++ source API exported by `cpp_wrapper`.
3. The Python API exported by `my_c_wrapper`.

The project version follows Semantic Versioning. `C_CORE_ABI_VERSION` is
incremented whenever an existing compiled C consumer must be rebuilt because
of removed symbols, changed signatures, changed calling conventions, or
incompatible public data layouts.

Additive exported functions do not require an ABI-version increment. Public
structs should use explicit size/version fields before they are stabilized.
Opaque handles are preferred because their layouts can evolve privately.

Every release must keep these values synchronized:

- `project(... VERSION ...)` in `CMakeLists.txt`;
- `[project].version` in `pyproject.toml`;
- `C_CORE_VERSION_*` in `c_lib/c_lib.h`;
- `my_c_wrapper.__version__`;
- `CHANGELOG.md`.

The shared library uses explicit symbol visibility plus `VERSION` and
`SOVERSION`. `tests/c/test_c_api.c`, the generated ctypes ABI check, and the
external CMake consumer protect the boundary.

