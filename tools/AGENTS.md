# AGENTS.md — tools/

This directory contains the binding pipeline scripts and the PEP 517 wheel
backend. These are implementation tools, not public API.

`sudo` is prohibited. Every script must reject execution outside an environment
created by `virtualenv`. Scripts in `tools/bindings/` call `require_virtualenv()`
from `common.py` at startup.

---

## Binding Pipeline

```
c_lib/c_lib.h + bindings/bindings.toml
         │
         ▼
tools/bindings/extract_api.py        → build/bindings/api.json
         │
         ▼
tools/bindings/generate_ctypes.py    → src/my_c_wrapper/_ctypes.py
         │
         ▼
tools/bindings/generate_abi.py       → build/bindings/abi_probe (compiled C probe)
         │
         ▼
tools/bindings/validate_abi.py       ← reads probe output, compares ctypes sizes
```

Run the whole pipeline:

```bash
just bindings
```

---

## extract_api.py — C Metadata Extractor

Invokes `clang -Xclang -ast-dump=json -fsyntax-only` on `c_lib/c_lib.h` and
produces `build/bindings/api.json`.

**What it extracts**:
- `functions` — name, parameters (name + C type), return type, source location.
- `records` — structs and unions. Only records referenced by included function
  signatures are kept; OS-internal types are excluded via `_referenced_record_names()`.
- `enums` — name and integer values.

**Filtering**:
- Only symbols from headers listed in `bindings/bindings.toml` `[headers]`.
- Only functions named in `[symbols] include` (and not in `[symbols] exclude`).

Do not modify `api.json` by hand. If the extractor emits an unexpected type,
add it to `[symbols] exclude` or fix the filter logic in `extract_api.py`.

---

## generate_ctypes.py — ctypes Code Generator

Reads `build/bindings/api.json` and `bindings/bindings.toml`, writes
`src/my_c_wrapper/_ctypes.py`.

**What it generates**:
- `ctypes` class stubs for each record.
- Integer constants for enum values (`C_CORE_OK = 0`, etc.).
- `_lib.fn_name.argtypes = [...]` and `_lib.fn_name.restype = ...` for each function.

**Type map** (C type → ctypes type):

| C type | ctypes type |
|--------|-------------|
| `int64_t` | `ctypes.c_int64` |
| `uint32_t` | `ctypes.c_uint32` |
| `int` | `ctypes.c_int` |
| `void *` | `ctypes.c_void_p` |
| `const char *` | `ctypes.c_char_p` |
| enum type | `ctypes.c_int` |
| `T *` (record pointer) | `ctypes.POINTER(T)` |

---

## generate_abi.py — C Probe Generator and Compiler

Generates a C program that uses `printf` to emit `sizeof` and `_Alignof`
for every type in `bindings/bindings.toml` `[abi]`, then compiles and runs it.

Output format:
```
sizeof(int)=4
alignof(int)=4
sizeof(void *)=8
```

Add a new type to `[abi]` when it enters the public API:

```toml
[abi]
scalars = ["int", "void *", "int64_t"]
records = ["CMyStruct"]
```

---

## validate_abi.py — ABI Checker

Reads the probe output and `_ctypes.py`, asserts that ctypes sizes and
alignments match the compiler's view. Fails loudly on any mismatch.

This catches platform divergence that compiles silently but causes memory
corruption at runtime.

---

## package_smoke.py — Isolated Install Tester

Creates two temporary virtualenv environments outside the repository:

1. **Editable install** — `pip install -e .` in a clean env.
2. **Wheel install** — builds the wheel, installs it in a clean env from
   outside the repository, verifies platform tag and native library presence.

Run with `just wheel` then `just package-smoke`.

---

## check_environment_policy.py — Policy Checker

Checks that all `AGENTS.md` files contain:
- `` `sudo` is prohibited `` (backtick-quoted; strips backticks before checking).
- `virtualenv`.

Prevents policy drift when new `AGENTS.md` files are added.

---

## native_build_backend/ — PEP 517 Wheel Backend

`backend.py` implements `build_wheel` and `build_sdist`:

1. Runs `cmake --preset native-wheel` and `cmake --build`.
2. Regenerates `api.json` and `_ctypes.py` against the fresh build.
3. Calls the standard `setuptools` backend.
4. Patches the wheel: replaces the generic platform tag with the platform-
   specific tag (`macosx_*_arm64`, `linux_x86_64`, `win_amd64`, etc.).
5. Rewrites `RECORD` hashes.

Use `just wheel` to invoke the backend. The output wheel filename must contain
a platform tag, not `none-any`.

---

## customize_template.py — Copier Post-Hook

Runs automatically after `copier copy`. Renames all placeholder strings:

- `MyProject` → cmake project name
- `my_c_wrapper` → Python package name
- `my-c-wrapper` → hyphenated PyPI name
- `c_lib` → C library name

Also renames `src/my_c_wrapper/` and `cmake/MyProjectConfig.cmake.in`.
Do not run manually on an existing (already-customized) project.
