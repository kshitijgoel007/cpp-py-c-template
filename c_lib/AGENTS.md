# AGENTS.md — c_lib/

This directory owns the implementation and the stable C ABI. Every other layer
in the repository depends on `c_lib.h`. A change here has downstream
consequences in the C++ wrapper, the Python binding pipeline, and every
packaged distribution of the library.

`sudo` is prohibited. Python generation and validation must run through
`.venv` (created with `virtualenv`).

---

## What This Layer Owns

| File | Purpose |
|------|---------|
| `c_lib.h` | Public ABI — the only file downstream consumers include |
| `c_lib.c` | Private implementation — internal struct definitions live here |

Do not put implementation logic in the header. Do not expose internal types
in the header.

---

## ABI Contract Rules

- Mark every exported symbol with the visibility macro defined at the top of
  `c_lib.h`. Without it the symbol is hidden by the `hidden` visibility preset
  and ctypes will not find it.
- Use fixed-width integer types from `<stdint.h>` (`int64_t`, `uint32_t`, etc.)
  whenever width is part of the contract.
- Use explicit output parameters for results that can fail:
  `StatusType my_fn(input, output_ptr)` not `output_type my_fn(input)`.
- Define every error condition for every function. Convention: 0 is success,
  negative values are errors. Add new codes to the status enum in `c_lib.h`
  rather than re-using existing codes with new semantics.
- Never return a pointer to stack storage or temporary data.
- Never expose C++ types, exceptions, templates, references, or overloads.
- Keep the `extern "C"` guard so C++ callers can include the header directly.

---

## Visibility Macro

The header defines a cross-platform visibility macro using the project's
chosen prefix. Look at the macro block at the top of `c_lib.h` for the exact
name. The pattern it follows:

```c
#ifndef YOUR_LIB_API
  #if defined(_WIN32)
    #ifdef YOUR_LIB_BUILDING_LIBRARY
      #define YOUR_LIB_API __declspec(dllexport)
    #else
      #define YOUR_LIB_API __declspec(dllimport)
    #endif
  #else
    #define YOUR_LIB_API __attribute__((visibility("default")))
  #endif
#endif
```

`CMakeLists.txt` defines the `_BUILDING_LIBRARY` compile definition when
compiling `c_lib.c` and sets `C_VISIBILITY_PRESET hidden`, so only symbols
annotated with the macro are exported.

---

## Adding a Stateless Function

```c
// c_lib.h — declare with a full contract comment
YOUR_LIB_API YourStatusType my_fn(int64_t a, int64_t b, int64_t *result);

// c_lib.c — implement; internal helpers need not be exported
YourStatusType my_fn(int64_t a, int64_t b, int64_t *result) {
    if (!result) return YOUR_INVALID_ARGUMENT_CODE;
    *result = a + b;
    return YOUR_OK_CODE;
}
```

`YOUR_LIB_API`, `YourStatusType`, and the status constants are the names
defined in `c_lib.h` for your project. The starter template uses `C_CORE_API`,
`CCoreStatus`, `C_CORE_OK`, etc. — these are renamed when you run copier.

After adding the declaration, update the full vertical slice described in the
root `AGENTS.md`.

---

## Adding an Opaque Resource

Opaque structs hide the implementation from callers; only `c_lib.c` sees the
full definition. The starter `CAccumulator` demonstrates this pattern.

```c
// c_lib.h — forward declaration only (opaque)
typedef struct CMyResource CMyResource;
C_CORE_API CMyResource *my_resource_create(int64_t initial);
C_CORE_API void         my_resource_destroy(CMyResource *r);  // NULL-safe
C_CORE_API CCoreStatus  my_resource_operate(CMyResource *r, int64_t value,
                                             int64_t *out);

// c_lib.c — private definition
struct CMyResource {
    int64_t state;
};

CMyResource *my_resource_create(int64_t initial) {
    CMyResource *r = malloc(sizeof(CMyResource));
    if (!r) return NULL;
    r->state = initial;
    return r;
}

void my_resource_destroy(CMyResource *r) {
    free(r);   // free(NULL) is defined no-op
}
```

Always document: who calls destroy, whether NULL is accepted, what happens if
destroy is called twice.

---

## Adding an Enum

Define in the header before any function that uses it. Give every value an
explicit integer so the binding generator sees the right constants.

```c
typedef enum {
    MY_ENUM_A = 0,
    MY_ENUM_B = 1,
    MY_ENUM_C = -1,
} CMyEnum;
```

Update `bindings.toml` if the enum values should appear as Python constants.
They are automatically extracted from the header.

---

## ABI Stability and Versioning

The CMake `VERSION` and `SOVERSION` properties live in `CMakeLists.txt`:

```cmake
set_target_properties(c_lib PROPERTIES
    VERSION   0.2.0   # full version → libc_lib.0.2.0.dylib
    SOVERSION 0       # major-only → libc_lib.0.dylib symlink
)
```

**Increment SOVERSION** when any of the following change:
- A function is removed or renamed.
- A parameter type, count, or order changes.
- A struct layout visible to callers changes.
- A status code is reused with a different meaning.

**Do not increment SOVERSION** for additions that do not alter existing
symbols, or for changes entirely inside `c_lib.c`.

After a SOVERSION bump, update `VERSION` in `CMakeLists.txt` and
`pyproject.toml`, then regenerate and re-validate the full binding stack.

---

## Validation

```bash
just build          # compiles c_lib and checks exported symbols
ctest --preset dev  # runs tests/c/test_c_api.c
just check          # full pipeline including ABI probe
```

To inspect exported symbols on macOS:
```bash
nm -gU build/dev/lib/libc_lib.dylib | grep "my_fn"
```
