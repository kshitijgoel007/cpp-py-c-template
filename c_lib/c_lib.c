#include "c_lib.h"
#include <stdio.h>

int add_integers(int a, int b)
{
  printf("[C]      Executing 'add_integers(%d, %d)'\n", a, b);
  return a + b;
}