# Python Binding Architecture

## Mandatory Environment Policy

`sudo` is prohibited. All Python generation, packaging, and validation runs
inside environments created with `virtualenv`. The repository environment is
`.venv`, created by `just env`; the package-smoke tool creates its temporary
environments with `python -m virtualenv`. The standard-library `venv` module
and global Python package installation are not supported workflows.

## Pipeline

The Python layer uses a policy-driven two-stage generation pipeline:

```text
c_lib/c_lib.h + bindings/bindings.toml
                  |
                  v
        build/bindings/api.json
                  |
                  v
       src/my_c_wrapper/_ctypes.py
                  |
                  v
       src/my_c_wrapper/wrapper.py
```

`api.json` contains normalized C facts extracted from Clang's JSON AST.
`bindings.toml` contains decisions that C syntax cannot express reliably:

- which functions form the Python binding surface;
- ownership of returned pointers;
- pointer/count relationships for arrays;
- callback lifetime rules;
- records and scalar types requiring ABI validation.

The generated `_ctypes.py` remains a low-level implementation detail.
`wrapper.py` is the stable Python API.

The starter package includes an opaque `CAccumulator` example. Its allocation
is owned by C, released by `accumulator_destroy()`, wrapped with RAII in C++,
and exposed as a context manager in Python. Generated status constants allow
the handwritten wrapper to translate overflow into `OverflowError`.

## Native Library Loading

`src/my_c_wrapper/_loader.py` searches in this order:

1. `MY_C_WRAPPER_LIBRARY`, when explicitly set;
2. the installed package's `lib/` directory;
3. beside the installed package;
4. known CMake build directories for source-tree development.

All candidates are absolute paths. Loading never depends on the process
working directory.

## ABI Validation

`tools/bindings/generate_abi.py` compiles and runs a C probe. The probe records:

- scalar sizes and alignments;
- configured structure and union sizes;
- configured structure and union alignments;
- field offsets.

`tools/bindings/validate_abi.py` compares those compiler-derived facts with
the generated `ctypes` declarations. Add every new by-value public record to
`bindings/bindings.toml` under `abi.records`.

## Wheels

The PEP 517 backend in `tools/native_build_backend/`:

1. configures and builds the C library with CMake;
2. regenerates API metadata and ctypes bindings;
3. bundles the platform library under `my_c_wrapper/lib/`;
4. changes the wheel from a pure-Python tag to a platform tag;
5. rewrites wheel metadata and `RECORD` hashes.

These wheels are platform-specific even though the Python code itself is
pure Python.

The template does not claim manylinux or macOS backward-compatibility tags.
Release projects should set an explicit deployment target and run platform
repair tooling such as `auditwheel`, `delocate`, or `delvewheel` when the C
library gains external shared-library dependencies.

## Validation Commands

```bash
just env
just build
just bindings
just check
just wheel
just package-smoke
```

`package-smoke` creates clean environments for editable and wheel installs.
It executes from outside the repository, verifies the wheel is not tagged as
pure Python, checks that the native library is present, and calls the public
Python API. `just test` additionally runs `tests/python/test_wrapper.py`.
