#ifndef C_LIB_H
#define C_LIB_H

#include <stdint.h>

#if defined(_WIN32)
#if defined(C_CORE_BUILDING_LIBRARY)
#define C_CORE_API __declspec(dllexport)
#else
#define C_CORE_API __declspec(dllimport)
#endif
#elif defined(__GNUC__) || defined(__clang__)
#define C_CORE_API __attribute__((visibility("default")))
#else
#define C_CORE_API
#endif

#define C_CORE_VERSION_YEAR 2026
#define C_CORE_VERSION_MONTH 6
#define C_CORE_VERSION_MICRO 0
#define C_CORE_VERSION_STRING "2026.6.1"
#define C_CORE_ABI_VERSION 1u

#ifdef __cplusplus
extern "C" {
#endif

typedef struct CAccumulator CAccumulator;

// Status values returned by checked core operations.
typedef enum CCoreStatus
{
  C_CORE_OK = 0,
  C_CORE_INVALID_ARGUMENT = -1,
  C_CORE_OVERFLOW = -2,
} CCoreStatus;

// Add two signed 64-bit integers and write the result. Returns OVERFLOW
// without writing a result when the sum cannot be represented by int64_t.
C_CORE_API CCoreStatus checked_add(int64_t a, int64_t b, int64_t* result);

// Allocate an accumulator with the supplied initial value. Returns NULL on
// allocation failure. Release the result with accumulator_destroy().
C_CORE_API CAccumulator* accumulator_create(int64_t initial_value);

// Release an accumulator. Passing NULL is allowed.
C_CORE_API void accumulator_destroy(CAccumulator* accumulator);

// Add value to the accumulator and write the new total. Returns OVERFLOW
// without changing state when the result cannot be represented by int64_t.
C_CORE_API CCoreStatus accumulator_add(CAccumulator* accumulator, int64_t value, int64_t* total);

// Write the current total. The accumulator and output pointer must be non-NULL.
C_CORE_API CCoreStatus accumulator_total(const CAccumulator* accumulator, int64_t* total);

// Return the ABI version and semantic version string of the loaded library.
C_CORE_API uint32_t core_abi_version(void);
C_CORE_API const char* core_version_string(void);

#ifdef __cplusplus
}
#endif

#endif  // C_LIB_H
