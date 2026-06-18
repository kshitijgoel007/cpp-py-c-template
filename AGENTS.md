# AGENTS.md — Repository Root

Mandatory reading for any agent working in this repository.
Nested `AGENTS.md` files in each directory add layer-specific rules that take precedence over this
file for files in their directory.

---

## Architecture

One C implementation, two independent consumer layers.

```
c_lib/c_lib.h  ←  the ABI contract (source of truth for every layer)
       │
       ├── c_lib/c_lib.c          C implementation (shared library)
       │
       ├── cpp_wrapper/           C++17 RAII adapter (static library)
       │
       └── bindings/bindings.toml + Clang AST
                │
                ▼
          build/bindings/api.json        ← normalized C facts (generated)
                │
                ▼
          src/my_c_wrapper/_ctypes.py    ← raw ctypes bindings (generated)
                │
                ▼
          src/my_c_wrapper/wrapper.py    ← handwritten Python API (source)
```

**Dependency rule**: C library → nothing. C++ wrapper → C library only.
Python layer → C library only. C++ and Python layers must never depend on
each other.

---

## File Map

| Path | Role | Edit? |
|------|------|-------|
| `c_lib/c_lib.h` | Public C ABI — foreign-function contract | Yes |
| `c_lib/c_lib.c` | C implementation | Yes |
| `bindings/bindings.toml` | Binding and ABI policy | Yes |
| `cpp_wrapper/cpp_wrapper.h` | Public C++ API | Yes |
| `cpp_wrapper/cpp_wrapper.cpp` | C++ implementation | Yes |
| `src/my_c_wrapper/wrapper.py` | Handwritten Python API | Yes |
| `src/my_c_wrapper/__init__.py` | Package exports | Yes |
| `src/my_c_wrapper/_loader.py` | Native library discovery | Rarely |
| `src/my_c_wrapper/_environment.py` | virtualenv enforcement | No |
| `src/my_c_wrapper/_ctypes.py` | Raw ctypes bindings | **Never** — generated |
| `src/my_c_wrapper/lib/` | Copied native library | **Never** — generated |
| `tests/c/test_c_api.c` | C API tests (CTest) | Yes |
| `tests/cpp/test_cpp_wrapper.cpp` | C++ tests (GoogleTest/CTest) | Yes |
| `tests/python/test_wrapper.py` | Python tests (pytest) | Yes |
| `tests/consumer/` | External `find_package` integration test | Rarely |
| `tools/bindings/` | Extraction, generation, ABI probe | Rarely |
| `build/` | CMake output | **Never** — generated |
| `main.cpp`, `main.py` | Consumer demos | Yes |
| `CMakeLists.txt` | Build system | Yes (for new targets) |
| `CMakePresets.json` | Named build presets | Rarely |
| `justfile` | Task runner | Yes (for new workflows) |
| `pyproject.toml` | Python package metadata and tool config | Yes |
| `copier.yml` | Template customization manifest | Rarely |

---

## Non-Negotiable Rules

- `sudo` is prohibited everywhere — in commands, scripts, CI, and suggestions.
- All Python runs in `.venv` created by `virtualenv`. No system interpreter,
  no stdlib `venv`.
- Never hand-edit `src/my_c_wrapper/_ctypes.py`. Regenerate with `just bindings`.
- Never commit `build/`, `src/my_c_wrapper/lib/`, `.venv/`, `dist/`,
  `src/my_c_wrapper/_ctypes.py`, or `*.egg-info`.
- A public C change is not done until C++, Python, and tests are all updated.

---

## Environment Setup

```bash
just env        # create .venv with virtualenv and install dev tools
just build      # cmake --preset dev + cmake --build --preset dev
just bindings   # extract api.json, generate _ctypes.py
just check      # build + test + lint + ABI + policy (the full gate)
```

The `just check` command is the definition of done. Run it before marking any
task complete.

---

## Starter Code

The template ships with a minimal working example — `checked_add` (a stateless
function) and `CAccumulator`/`Accumulator` (an opaque resource) — that
demonstrates the patterns across all three layers. These are meant to be
replaced by your own operations once you understand the structure. Do not
build on top of the starter names; delete or replace them as you add your own
API.

---

## Change Recipe: Add a New Public Function

Follow this order exactly. Skipping a layer leaves the codebase inconsistent.

### 1. C declaration — `c_lib/c_lib.h`

Declare the function using the visibility macro already defined in the header,
a status return type, and explicit output parameters:

```c
// Document: parameters, return value, ownership, error conditions, nullability.
YOUR_API_MACRO YourStatusType my_function(int64_t input, int64_t *output);
```

Use fixed-width integer types (`int64_t`, `uint32_t`, etc.), no C++ types,
and no raw return of computed values that can fail. See the visibility macro
and status enum already in `c_lib.h` for the exact names defined for your
project.

### 2. C implementation — `c_lib/c_lib.c`

```c
YourStatusType my_function(int64_t input, int64_t *output) {
    if (!output) return YOUR_INVALID_ARGUMENT_CODE;
    *output = input * 2;
    return YOUR_OK_CODE;
}
```

### 3. Binding policy — `bindings/bindings.toml`

Add the function name to `[symbols] include`:

```toml
[symbols]
include = [
    "my_function",   # ← add here
    ...
]
```

If the function returns an owned pointer, add to `[ownership]`:

```toml
[ownership]
my_function = "owned:my_destructor"
```

### 4. Regenerate bindings

```bash
just bindings
```

This updates `build/bindings/api.json` and `src/my_c_wrapper/_ctypes.py`.
Verify `_ctypes.py` now contains `my_function` with correct `restype`/`argtypes`.

### 5. C++ wrapper — `cpp_wrapper/cpp_wrapper.h` + `.cpp`

Add a member function to whichever C++ class groups this operation, or add a
free function if the operation does not belong to any existing class:

```cpp
// In header:
std::int64_t my_function(std::int64_t input);

// In .cpp:
std::int64_t YourClass::my_function(std::int64_t input) {
    std::int64_t result{};
    auto status = ::my_function(input, &result);
    if (status != YOUR_OK_CODE)
        throw std::runtime_error("my_function failed");
    return result;
}
```

Translate every non-OK status to the most specific exception type. For owned
resources, use the RAII pattern described in `cpp_wrapper/AGENTS.md`.

### 6. Python wrapper — `src/my_c_wrapper/wrapper.py`

```python
def my_function(input):
    """Return double the input."""
    result = ctypes.c_int64()
    status = _ctypes.my_function(
        _checked_integer(input, bits=64, name="input"),
        ctypes.byref(result),
    )
    if status != _ctypes.YOUR_OK_CONSTANT:
        raise RuntimeError("my_function failed")
    return result.value
```

### 7. Export — `src/my_c_wrapper/__init__.py`

```python
from .wrapper import ..., my_function

__all__ = [..., "my_function"]
```

### 8. Tests

- `tests/c/test_c_api.c` — call the C function directly, check status codes
  and output values.
- `tests/cpp/test_cpp_wrapper.cpp` — call through the C++ wrapper, check
  return values and that exceptions are raised on error.
- `tests/python/test_wrapper.py` — call through the Python API, check return
  values and that Python exceptions are raised.

### 9. Validate

```bash
just check
```

All CTests and all pytest tests must pass.

---

## Change Recipe: Add an Opaque Resource (Create/Destroy/Operate)

The starter `CAccumulator`/`Accumulator` demonstrates this pattern end-to-end
across all three layers. Read it as a reference, then follow these steps for
your own resource type.

1. **C header**: declare an incomplete struct (`typedef struct CMyThing CMyThing`),
   and create/destroy/operate functions with explicit ownership documentation.
2. **C impl**: define the struct privately in `.c`, implement lifecycle functions.
3. **bindings.toml**: add all functions to `[symbols]`, add the create function
   to `[ownership]` pointing at its destroy function.
4. **Regenerate**: `just bindings`.
5. **C++ wrapper**: wrap with RAII — constructor calls create and throws on
   allocation failure, destructor calls destroy (which must be NULL-safe),
   operations translate status codes to exceptions. Delete copy, implement move.
6. **Python wrapper**: write a class with `close()`, `__enter__`/`__exit__`,
   and `__del__`. Validate and range-check all inputs before passing to ctypes.
7. **Tests**: cover happy path, error conditions, context-manager cleanup,
   idempotent close, and operations after close.

---

## Change Recipe: Customize the Template (New Project)

```bash
pip install copier
copier copy /path/to/this-template /path/to/new-project
# Answer the prompts: project_name, cmake_name, python_package, etc.
cd /path/to/new-project
just env
just check
```

`copier` runs `tools/customize_template.py` automatically. It renames every
placeholder string (`MyProject`, `my_c_wrapper`, `my-c-wrapper`, etc.) to the
values you provided and renames the source directory and cmake config file.

After customization, the project is independent. Do not modify the original
template repository.

---

## Definition of Done

A change is complete when all of the following hold:

- [ ] Public behavior is represented consistently in every affected language
      layer (C header, C++ wrapper, Python wrapper, exports).
- [ ] `just check` passes with no failures and no lint errors.
- [ ] `src/my_c_wrapper/_ctypes.py` was regenerated and matches the current
      C header but is **not** staged for commit.
- [ ] `src/my_c_wrapper/lib/` is **not** staged for commit.
- [ ] `git status --short` shows only intentional source changes.
- [ ] No command required elevated privileges.
- [ ] Every Python command ran inside a `virtualenv` environment.
