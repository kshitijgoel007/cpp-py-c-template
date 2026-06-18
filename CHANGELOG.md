# Changelog

All notable changes are documented here. This project uses Calendar Versioning
(`YYYY.M.MICRO`). The C ABI has a separate integer version exposed by
`core_abi_version()` and tracked as `C_CORE_ABI_VERSION` in `c_lib.h` and
`C_CORE_ABI_VERSION` in `CMakeLists.txt`.


- Added the checked arithmetic and opaque accumulator starter APIs.
- Added generated policy-driven ctypes bindings and native Python wheels.

## v2026.6.1 (2026-06-18)

## v2026.6.0 (2026-06-18)

### Feat

- switch to Calendar Versioning (YYYY.M.MICRO) and fix CI

## v0.3.1 (2026-06-18)

### Fix

- exclude cmake_consumer from sanitizer and coverage ctest runs

## v0.3.0 (2026-06-18)

### Feat

- complete template infrastructure and agentic workflow documentation

### Fix

- native library copy now uses unversioned linker name (libc_lib.dylib)
fix: binding extractor no longer leaks OS-internal struct types into _ctypes.py
fix: environment policy checker handles backtick-quoted sudo in AGENTS.md

### Refactor

- remove mypy and all type annotations (project targets Python 3.11+)
refactor: remove from __future__ import annotations throughout
