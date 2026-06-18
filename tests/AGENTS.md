# AGENTS.md — tests/

This directory contains all test code. Each subdirectory tests one layer at the
appropriate level of abstraction.

`sudo` is prohibited. Python tests run inside `.venv`, created by `virtualenv`.

---

## Test Layer Map

| Directory | Runner | Tests |
|-----------|--------|-------|
| `tests/c/` | CTest | C ABI directly — status codes, output values, null safety |
| `tests/cpp/` | GoogleTest/CTest | C++ wrapper — exceptions, RAII lifecycle, move semantics |
| `tests/python/` | pytest | Python public API — Python exceptions, context manager, idempotent close |
| `tests/consumer/` | CTest (cmake) | External `find_package(MyProject)` consumer — integration |

Run the full test suite:

```bash
just test     # CTest + pytest + both demos
just check    # build + just test + lint + ABI + policy
```

---

## tests/c/ — C API Tests

- Use the public `c_lib.h` header only. No access to private struct definitions.
- Test every status code a function can return.
- Test null-pointer handling for every nullable parameter.
- Test boundary values: `INT64_MAX`, `INT64_MIN`, zero, and values that cause
  overflow.
- Test that `accumulator_destroy(NULL)` is safe (no crash).

```c
static void test_checked_add_overflow(void) {
    int64_t result;
    CCoreStatus s = checked_add(INT64_MAX, 1, &result);
    assert(s == C_CORE_OVERFLOW);
}
```

---

## tests/cpp/ — C++ Wrapper Tests

Use GoogleTest. Tests are registered as the `cpp_wrapper_tests` CTest target.

**Stateless operations**: Verify return values for valid inputs; verify that
the correct exception type (`std::overflow_error`, `std::runtime_error`) is
thrown for each error condition.

**RAII resources**: Cover all lifecycle paths:

```cpp
// Constructed and destroyed normally
TEST(AccumulatorTest, ConstructAndDestroy) {
    Accumulator acc(10);
    EXPECT_EQ(acc.add(5), 15);
}  // acc.~Accumulator() calls accumulator_destroy

// Move semantics
TEST(AccumulatorTest, MoveTransfersOwnership) {
    Accumulator a(0);
    Accumulator b(std::move(a));
    EXPECT_EQ(b.add(1), 1);
}

// Exception on overflow
TEST(AccumulatorTest, AddOverflowThrows) {
    Accumulator acc(std::numeric_limits<int64_t>::max());
    EXPECT_THROW(acc.add(1), std::overflow_error);
}
```

---

## tests/python/ — Python Public API Tests

Use pytest. Tests must import from `my_c_wrapper`, not from internal modules.
Never test `_ctypes` symbols directly.

**Required coverage for every public function**:

1. Happy path — correct return value.
2. Wrong type input — `TypeError`.
3. Out-of-range input — `OverflowError`.

**Required coverage for every resource class**:

1. Happy path — create, operate, close.
2. Context manager — `__enter__`/`__exit__` closes on exit.
3. Overflow during operation — `OverflowError`, state preserved after overflow.
4. Idempotent close — `close()` twice is safe; operations after close raise
   `RuntimeError` with "closed" in the message.
5. Input validation — `OverflowError` on out-of-range constructor arg.

`tests/python/test_wrapper.py` is the reference implementation of all five
scenarios for `Accumulator`.

---

## tests/consumer/ — External Consumer Test

This is a minimal CMake project that calls `find_package(MyProject)` against
an installed prefix. It must never include headers from the build tree.

The `tests/run_consumer_test.cmake.in` script installs the project into a temp
prefix, then configures and builds the consumer. This is registered as CTest
`cmake_consumer`. Do not break this test when modifying CMake targets or
install rules. The install path uses `${CMAKE_INSTALL_INCLUDEDIR}` (not a
project-specific subdirectory) so `#include <cpp_wrapper.h>` resolves directly.

---

## Adding Tests for a New Operation

1. **C test** (`tests/c/test_c_api.c`): Add a `test_<name>_<scenario>` function
   for each status code the C function can return. Check output values and status.

2. **C++ test** (`tests/cpp/test_cpp_wrapper.cpp`): Add `TEST` blocks for each
   exception type and for successful return values.

3. **Python test** (`tests/python/test_wrapper.py`): Add `def test_<name>_<scenario>`
   functions. Import only from `my_c_wrapper`.

4. For new resource classes: add all five lifecycle scenarios described above.
