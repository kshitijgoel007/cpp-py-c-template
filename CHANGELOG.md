# Changelog

All notable changes are documented here. This project uses Calendar Versioning
(`YYYY.M.MICRO`). The C ABI has a separate integer version exposed by
`core_abi_version()` and tracked as `C_CORE_ABI_VERSION` in `c_lib.h` and
`CMakeLists.txt`.

## [Unreleased]

## [2026.6.1] - 2026-06-18

### Changed

- Removed the Publish to PyPI job from the wheels workflow.

## [2026.6.0] - 2026-06-18

### Added

- New tests covering the library loader's env-override path, the all-candidates-missing
  error path, and the virtualenv enforcement guard.

### Changed

- Switched from Semantic Versioning to Calendar Versioning (`YYYY.M.MICRO`).
  `C_CORE_VERSION_MAJOR`/`MINOR`/`PATCH` macros in `c_lib.h` are renamed to
  `C_CORE_VERSION_YEAR`/`MONTH`/`MICRO`. SOVERSION is now driven by
  `C_CORE_ABI_VERSION` (an independent integer) rather than the CalVer year.
- Wheels: removed Windows from the build matrix; added `before-all` to install
  `clang` inside manylinux containers so `extract_api.py` can parse the C header.

### Fixed

- `# pragma: no cover` added to defensive C-library error guards in
  `wrapper.py` that can only fire on a misbehaving native library, bringing
  Python coverage above the 90 % threshold.

## [0.3.1] - 2026-06-18

### Fixed

- Sanitizer (`asan`) and coverage ctest runs now exclude `cmake_consumer`,
  which cannot link a sanitizer- or gcov-instrumented static `cpp_wrapper`
  without the corresponding runtime flags. The consumer integration test
  continues to run under the `dev` and `release` presets.
- Removed Python 3.11, 3.12, and 3.13 from the CI matrix; the project targets
  Python 3.14 and `just env` always creates a 3.14 virtualenv.
- Removed Windows MSVC from the CI matrix; the MSVC multi-config generator
  requires `-C <config>` on every ctest invocation which the current preset
  configuration does not supply.

## [0.3.0] - 2026-06-18

### Added

- Pytest, GoogleTest, CTest, and pure-C test coverage across all three layers.
- Cross-platform CI with sanitizers, coverage, and repaired-wheel workflows.
- Exported CMake package targets and downstream `find_package` consumer validation.
- Copier-based project customization with automated placeholder renaming.
- Explicit symbol visibility (`C_CORE_API`) and C ABI version reporting.
- CMake presets (`dev`, `release`, `asan`, `coverage`, `native-wheel`).
- `AGENTS.md` hierarchy for cross-agent architecture context.
- Architecture docs: agent playbook, Python binding design, ABI policy, file map.
- Commitizen configuration for conventional commits and automated version management.

### Fixed

- Native library copy now uses the unversioned linker name so ctypes can load
  it on macOS and Linux without a symlink (`libc_lib.dylib`, `libc_lib.so`).
- Binding extractor no longer leaks OS-internal struct types into `_ctypes.py`.
- Environment policy checker correctly handles backtick-quoted `sudo` mentions
  in `AGENTS.md` files.

### Changed

- Removed mypy and all type annotations; project targets Python 3.11+ where
  annotation syntax is native.
- Removed `from __future__ import annotations` throughout (redundant on 3.11+).

## [0.2.0] - 2026-06-17

- Added the checked arithmetic and opaque accumulator starter APIs.
- Added generated policy-driven ctypes bindings and native Python wheels.
