# AGENTS.md — cpp_wrapper/

This directory owns the C++17 adapter layer. It translates the C ABI into safe,
idiomatic C++ with RAII ownership and exception-based error handling.

`sudo` is prohibited. Install and validate only under user-writable prefixes.
Python-backed tooling must run through `.venv` (created with `virtualenv`).

---

## What This Layer Owns

| File | Purpose |
|------|---------|
| `cpp_wrapper.h` | Public C++ API — what downstream C++ consumers include |
| `cpp_wrapper.cpp` | C++ implementation |

This layer must not depend on any Python tooling, generated files, or internal
C structs. It depends only on `c_lib/c_lib.h` and the C++17 standard library.

---

## Design Rules

- All computation stays in `c_lib/`. This layer owns C++ ergonomics, resource
  management, and error translation only.
- Use RAII for every resource acquired through the C API.
- Never let C++ exceptions cross the C boundary. Never call C++ functions from
  inside C callbacks exposed to the C layer.
- The public header must be self-contained: it includes what it uses and
  compiles cleanly for a downstream consumer who has no access to `c_lib/`
  internals.
- Include `c_lib.h` with an explicit path or via the installed include
  directory; do not rely on relative include tricks.
- Preserve const-correctness throughout.
- Delete copy constructor and copy assignment for RAII resource holders.
  Provide move constructor and move assignment.
- Document which C++ exceptions each public operation may throw.

---

## Pattern: Stateless Function

Group related stateless operations in a class with only member functions, or
expose them as free functions if they do not belong to a coherent object.

The starter template's `Calculator` class shows this pattern. Replace it with
your own class name and operations.

```cpp
// cpp_wrapper.h
class YourService {
public:
    std::int64_t compute(std::int64_t a, std::int64_t b);
};

// cpp_wrapper.cpp
std::int64_t YourService::compute(std::int64_t a, std::int64_t b) {
    std::int64_t result{};
    auto status = ::c_compute(a, b, &result);
    if (status == YOUR_OVERFLOW_CODE)
        throw std::overflow_error("compute: integer overflow");
    if (status != YOUR_OK_CODE)
        throw std::runtime_error("compute: unexpected error");
    return result;
}
```

Translate every non-OK status code to the most specific appropriate exception.
Never silently return a default value on error.

---

## Pattern: Owned Resource (RAII)

Use a class that exclusively owns a C opaque handle. The starter template's
`Accumulator` class shows this pattern end-to-end.

```cpp
// cpp_wrapper.h
class YourResource {
public:
    explicit YourResource(/* construction args */);
    ~YourResource();

    // Move-only: copy is disabled because the C handle is not reference-counted.
    YourResource(YourResource &&other) noexcept;
    YourResource &operator=(YourResource &&other) noexcept;
    YourResource(const YourResource &) = delete;
    YourResource &operator=(const YourResource &) = delete;

    std::int64_t operate(std::int64_t value);

private:
    CYourHandle *handle_{nullptr};
};

// cpp_wrapper.cpp
YourResource::YourResource(/* args */)
    : handle_(your_handle_create(/* args */)) {
    if (!handle_)
        throw std::bad_alloc{};
}

YourResource::~YourResource() {
    your_handle_destroy(handle_);  // must be NULL-safe in C
}

YourResource::YourResource(YourResource &&other) noexcept
    : handle_(other.handle_) {
    other.handle_ = nullptr;
}

YourResource &YourResource::operator=(YourResource &&other) noexcept {
    if (this != &other) {
        your_handle_destroy(handle_);
        handle_ = other.handle_;
        other.handle_ = nullptr;
    }
    return *this;
}

std::int64_t YourResource::operate(std::int64_t value) {
    std::int64_t out{};
    auto status = your_handle_operate(handle_, value, &out);
    if (status == YOUR_OVERFLOW_CODE)
        throw std::overflow_error("operate: overflow");
    if (status != YOUR_OK_CODE)
        throw std::runtime_error("operate: error");
    return out;
}
```

Key invariants:
- Constructor throws `std::bad_alloc` if C allocation fails — never returns a
  half-initialized object.
- The C destroy function must be NULL-safe. The destructor calls it
  unconditionally.
- Move constructor/assignment null out the source handle so the moved-from
  destructor is a safe no-op.

---

## CMake Targets

The C++ wrapper is a static library that links publicly against `MyProject::core`:

```cmake
add_library(cpp_wrapper STATIC cpp_wrapper/cpp_wrapper.cpp)
target_link_libraries(cpp_wrapper PUBLIC MyProject::core)
target_include_directories(cpp_wrapper PUBLIC
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/cpp_wrapper>"
    "$<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>"
)
```

Downstream consumers use `target_link_libraries(my_target PRIVATE MyProject::cpp_wrapper)`.
They receive `c_lib.h` and `cpp_wrapper.h` transitivly.

---

## Validation

```bash
just build
./build/dev/bin/cpp_demo           # exercises the C++ API end-to-end
ctest --preset dev                  # runs GoogleTest suite and cmake_consumer
```

After a public header change, verify that `tests/consumer/main.cpp` still
compiles — it is a minimal downstream consumer that uses only installed headers.
