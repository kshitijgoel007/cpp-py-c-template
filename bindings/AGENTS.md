# AGENTS.md — bindings/

This directory contains `bindings.toml`, the source-controlled policy file for
the Python binding pipeline. C declarations are the source of truth for types
and signatures; `bindings.toml` records decisions that C syntax cannot express.

`sudo` is prohibited. All pipeline tools that read this file run through `.venv`
(created with `virtualenv`).

---

## File: bindings.toml

After any change to `bindings.toml`, regenerate and validate:

```bash
just bindings
```

---

## Section Reference

### `[headers]`

Which C headers the Clang AST extractor parses.

```toml
[headers]
include = ["c_lib/c_lib.h"]
```

Only include the public ABI header. Do not list internal headers or system
headers here — the extractor already visits all transitively included files,
but only extracts symbols that originate in these listed files.

---

### `[symbols]`

Which function names from the parsed headers form the Python binding surface.

```toml
[symbols]
include = [
    "your_function",       # stateless operation
    "your_resource_create",
    "your_resource_destroy",
    "your_resource_operate",
    "lib_abi_version",     # always keep version introspection functions
    "lib_version_string",
]
exclude = []
```

The starter template ships with `checked_add`, `accumulator_*`, `core_abi_version`,
and `core_version_string` in this list. Replace the starter entries with your
own function names as you build out your API.

**`include`**: Only functions listed here appear in `_ctypes.py`. Add a
function here when adding it to the Python API. Add it to `include` at the
same time as adding the handwritten wrapper in `wrapper.py`.

**`exclude`**: Functions that are in the header but must not be exposed to
Python. Use this for C-only internal utilities or symbols not ready for Python.

---

### `[abi]`

Types for which the ABI probe validates `sizeof` and `_Alignof` at build time.

```toml
[abi]
scalars = ["int", "void *"]
records = []
```

**`scalars`**: Primitive and pointer types. These must match `ctypes` size
assumptions on the target platform.

**`records`**: Struct or union types that appear in the public API by value.
Opaque handle types passed only by pointer do not need to be here because
ctypes only stores a pointer to them, not their layout.

Add a record here when a struct is passed or returned by value in the API.
The ABI probe will check field offsets as well as total size and alignment.

Example — add a new struct:

```toml
[abi]
scalars = ["int", "void *"]
records = ["CMyResult"]
```

---

### `[ownership]`

Documents which functions return heap-allocated C objects that the caller must
destroy. The generator uses this to document ownership in `_ctypes.py`.

```toml
[ownership]
your_resource_create = "owned:your_resource_destroy"
```

Format: `function_name = "owned:destroy_function_name"`.

The starter template has `accumulator_create = "owned:accumulator_destroy"`.
Replace it with your own create/destroy pair.

When a create-function appears here, the generated binding leaves `restype`
as a raw ctypes pointer (not a destructor-wrapped type). The handwritten Python
wrapper in `wrapper.py` is responsible for calling the destroy function.

Add an entry whenever a function allocates memory that the caller must free.

---

### `[arrays]`

Documents pointer/count parameter relationships for array arguments.

```toml
[arrays]
# my_batch_function.data = "count"
```

Format: `function_name.pointer_param = "count_param_name"`.

The binding generator and handwritten wrapper use this to know how many
elements the pointer points to. Leave this section empty until array-taking
functions enter the API.

---

### `[callbacks]`

Documents the lifetime of callback function pointers.

```toml
[callbacks]
# my_register_callback.callback = "persistent"
# my_call_once.callback = "transient"
```

Values: `"transient"` (callback is used only during the call) or
`"persistent"` (callback is stored and may be called after the function
returns). The Python wrapper must keep a reference to persistent callbacks to
prevent garbage collection.

Leave this section empty until callback-taking functions enter the API.

---

## Complete Example: Adding a New Function

Suppose you add `compute(int64_t x, int64_t *out)` to `c_lib.h`.

**1. Add to `[symbols] include`**:

```toml
[symbols]
include = [
    "compute",   # ← new
    ...          # your other functions
]
```

**2. If `compute` returns an owned pointer, add to `[ownership]`**:

```toml
[ownership]
# Not needed for this example — it returns a status code, not a pointer.
```

**3. Regenerate**:

```bash
just bindings
```

**4. Verify** `_ctypes.py` contains:

```python
_lib.compute.argtypes = [ctypes.c_int64, ctypes.POINTER(ctypes.c_int64)]
_lib.compute.restype = ctypes.c_int
```

**5. Continue** with the Python wrapper in `wrapper.py` as described in
`src/my_c_wrapper/AGENTS.md`.
