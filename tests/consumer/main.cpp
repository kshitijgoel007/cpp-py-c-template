#include <my_project/cpp_wrapper.h>

int main()
{
  Calculator calculator;
  Accumulator accumulator(40);
  return calculator.add(20, 22) == 42 && accumulator.add(2) == 42 ? 0 : 1;
}

