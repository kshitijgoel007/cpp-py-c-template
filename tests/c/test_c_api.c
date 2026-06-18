#include "c_lib.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

int main(void)
{
  int64_t result = 0;
  assert(checked_add(20, 22, &result) == C_CORE_OK);
  assert(result == 42);
  assert(checked_add(INT64_MAX, 1, &result) == C_CORE_OVERFLOW);

  CAccumulator* accumulator = accumulator_create(40);
  assert(accumulator != NULL);
  assert(accumulator_add(accumulator, 2, &result) == C_CORE_OK);
  assert(result == 42);
  assert(accumulator_total(accumulator, &result) == C_CORE_OK);
  assert(result == 42);
  accumulator_destroy(accumulator);

  assert(core_abi_version() == C_CORE_ABI_VERSION);
  assert(strcmp(core_version_string(), C_CORE_VERSION_STRING) == 0);
  return 0;
}
