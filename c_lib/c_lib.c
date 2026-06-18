#include "c_lib.h"

#include <stdint.h>
#include <stdlib.h>

struct CAccumulator
{
  int64_t total;
};

CCoreStatus checked_add(int64_t a, int64_t b, int64_t* result)
{
  if (result == NULL)
  {
    return C_CORE_INVALID_ARGUMENT;
  }
  if ((b > 0 && a > INT64_MAX - b) || (b < 0 && a < INT64_MIN - b))
  {
    return C_CORE_OVERFLOW;
  }
  *result = a + b;
  return C_CORE_OK;
}

CAccumulator* accumulator_create(int64_t initial_value)
{
  CAccumulator* accumulator = malloc(sizeof(CAccumulator));
  if (accumulator == NULL)
  {
    return NULL;
  }
  accumulator->total = initial_value;
  return accumulator;
}

void accumulator_destroy(CAccumulator* accumulator)
{
  free(accumulator);
}

CCoreStatus accumulator_add(CAccumulator* accumulator, int64_t value, int64_t* total)
{
  if (accumulator == NULL || total == NULL)
  {
    return C_CORE_INVALID_ARGUMENT;
  }
  if ((value > 0 && accumulator->total > INT64_MAX - value) ||
      (value < 0 && accumulator->total < INT64_MIN - value))
  {
    return C_CORE_OVERFLOW;
  }
  accumulator->total += value;
  *total = accumulator->total;
  return C_CORE_OK;
}

CCoreStatus accumulator_total(const CAccumulator* accumulator, int64_t* total)
{
  if (accumulator == NULL || total == NULL)
  {
    return C_CORE_INVALID_ARGUMENT;
  }
  *total = accumulator->total;
  return C_CORE_OK;
}

uint32_t core_abi_version(void)
{
  return C_CORE_ABI_VERSION;
}

const char* core_version_string(void)
{
  return C_CORE_VERSION_STRING;
}
