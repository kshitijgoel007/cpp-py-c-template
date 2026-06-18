# AGENTS.md — src/my_c_wrapper/

This directory is the Python package. It has two distinct parts:
- **Generated** — `_ctypes.py` and `lib/`. Never edit these by hand.
- **Handwritten** — `wrapper.py`, `__init__.py`, `_loader.py`, `_environment.py`.

`sudo` is prohibited. Every Python command and test must run inside `.venv`
(created with `virtualenv`).

---

## File Roles

| File | Edit? | Purpose |
|------|-------|---------|
| `wrapper.py` | Yes | Stable Python API — documented, raises Python exceptions |
| `__init__.py` | Yes | Exports the public surface |
| `_ctypes.py` | **Never** | Generated raw ctypes bindings — regenerate with `just bindings` |
| `_loader.py` | Rarely | Library discovery: env var → package `lib/` → CMake build dirs |
| `_environment.py` | No | Enforces virtualenv-only policy at import time |
| `lib/` | **Never** | Copied native library (`libc_lib.dylib`, `libc_lib.so`, `c_lib.dll`) |

---

## Binding Pipeline (How `_ctypes.py` Is Produced)

```
c_lib/c_lib.h  +  bindings/bindings.toml
                        │
            tools/bindings/extract_api.py
                (Clang JSON AST parser)
                        │
                        ▼
            build/bindings/api.json       ← normalized C metadata
                        │
            tools/bindings/generate_ctypes.py
                        │
                        ▼
            src/my_c_wrapper/_ctypes.py   ← raw ctypes (generated)
                        │
            tools/bindings/validate_abi.py
            (compiled C probe checks sizes/alignments)
```

Regenerate whenever `c_lib/c_lib.h` or `bindings/bindings.toml` change:

```bash
just bindings
```

Do not commit `_ctypes.py` or `lib/`.

---

## Adding a Stateless Function

**Step 1**: Add to `bindings/bindings.toml` `[symbols] include`:

```toml
[symbols]
include = ["my_function", ...]
```

**Step 2**: Regenerate.

```bash
just bindings
```

Verify `_ctypes.py` now has `my_function` with correct `argtypes` and `restype`.

**Step 3**: Add to `wrapper.py`.

```python
def my_function(a, b):
    """Return the result of the operation."""
    result = ctypes.c_int64()
    status = _ctypes.my_function(
        _checked_integer(a, bits=64, name="a"),
        _checked_integer(b, bits=64, name="b"),
        ctypes.byref(result),
    )
    if status == _ctypes.YOUR_OVERFLOW_CONSTANT:
        raise OverflowError("my_function: overflow")
    if status != _ctypes.YOUR_OK_CONSTANT:
        raise RuntimeError("my_function failed")
    return result.value
```

**Step 4**: Export from `__init__.py`.

```python
from .wrapper import ..., my_function

__all__ = [..., "my_function"]
```

---

## Adding a Resource Class (Opaque Handle / Context Manager)

The starter `Accumulator` in `wrapper.py` demonstrates this pattern end-to-end.
Read it as a reference, then follow the same structure for your own resource:

```python
class MyResource:
    """Own a C-allocated resource. Release with close() or via context manager."""

    def __init__(self, initial):
        self._handle = None   # set None first so __del__ is safe before create
        self._handle = _ctypes.my_resource_create(
            _checked_integer(initial, bits=64, name="initial")
        )
        if not self._handle:
            raise MemoryError("C library could not allocate MyResource")

    @property
    def closed(self):
        return self._handle is None

    def _require_open(self):
        if self._handle is None:
            raise RuntimeError("resource is closed")
        return self._handle

    def operate(self, value):
        """Perform the operation and return the result."""
        out = ctypes.c_int64()
        status = _ctypes.my_resource_operate(
            self._require_open(),
            _checked_integer(value, bits=64, name="value"),
            ctypes.byref(out),
        )
        if status == _ctypes.YOUR_OVERFLOW_CONSTANT:
            raise OverflowError("operate: overflow")
        if status != _ctypes.YOUR_OK_CONSTANT:
            raise RuntimeError("operate failed")
        return out.value

    def close(self):
        """Release the C resource. Calling this twice is safe."""
        if self._handle is not None:
            _ctypes.my_resource_destroy(self._handle)
            self._handle = None

    def __enter__(self):
        self._require_open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        self.close()
```

Key invariants:
- Set `self._handle = None` before calling `create` so `__del__` is safe if
  `create` raises.
- `close()` sets `_handle = None` after destroy so `__del__` is idempotent.
- `_require_open()` raises `RuntimeError("... is closed")` — the test suite
  checks for this exact phrase pattern.

---

## Input Validation Pattern

Use `_checked_integer` from `wrapper.py` for all integer inputs:

```python
def _checked_integer(value, *, bits, name):
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1
    if not minimum <= value <= maximum:
        raise OverflowError(f"{name} does not fit in a signed {bits}-bit integer")
    return value
```

This raises `TypeError` for non-integers and `OverflowError` for out-of-range
values before the value ever reaches ctypes.

---

## Native Library Discovery

`_loader.py` searches in this order:

1. `MY_C_WRAPPER_LIBRARY` environment variable (explicit override).
2. Package `lib/` directory (installed wheel path).
3. Package directory itself (fallback).
4. Known CMake build directories (`build/lib/`, `build/dev/lib/`,
   `build/release/lib/`, `build/native-wheel/lib/`).

When `just build` runs, the cmake post-build step copies the native library
from the build output into `src/my_c_wrapper/lib/`. This means development
workflow works without installing the wheel.

On macOS the loader searches for `libc_lib.dylib` (unversioned). The cmake
post-build copy uses `$<TARGET_LINKER_FILE_NAME:c_lib>` to produce this name.

---

## Package Policy

- No runtime dependencies outside the standard library.
- This package runs only inside `virtualenv` environments. `_environment.py`
  checks this at import time and raises `RuntimeError` if violated.
- No wildcard exports. Every public name must appear in `__init__.py`'s
  `__all__`.
- Do not add `from __future__ import annotations`. The package targets
  Python 3.11+, where all annotation syntax is native.
- Do not add type annotations. The project does not use mypy or any type
  checker.
- Convert every C status code into a specific Python exception. Never silently
  discard errors or return sentinel values.

---

## Validation

```bash
just bindings   # regenerate _ctypes.py and run ABI probe
just check      # build + test + lint + ABI + policy
```

If packaging metadata or native-library placement changes, also run:

```bash
just package-smoke
```

This creates isolated environments and verifies the wheel is platform-tagged,
the native library is present, and the public API is callable from outside the
repository.
