#include "cpp_wrapper.h"
#include <iostream>
#include <utility>

int main()
{
  std::cout << "[C++] C++ Executable Demo" << std::endl;
  Calculator calc;
  std::int64_t a = 100;
  std::int64_t b = 23;
  std::int64_t result = calc.add(a, b);
  std::cout << "[C++] " << a << " + " << b << " = " << result << std::endl;

  Accumulator accumulator(10);
  accumulator.add(5);
  accumulator.add(-2);
  Accumulator moved = std::move(accumulator);
  std::cout << "[C++] Moved accumulator total: " << moved.total() << std::endl;
  std::cout << "[C++] C++ Executable Finished" << std::endl;
  return 0;
}
