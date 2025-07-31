#include "cpp_wrapper.h"
#include <iostream>

int main()
{
  std::cout << "[C++] C++ Executable Demo" << std::endl;
  std::cout << "[C++] Creating Calculator object from C++ code." << std::endl;
  Calculator calc;
  int a = 100;
  int b = 23;
  std::cout << "[C++] Calling calc.add(" << a << ", " << b << ")" << std::endl;
  int result = calc.add(a, b);
  std::cout << "[C++] Result: " << result << std::endl;
  std::cout << "[C++] C++ Executable Finished" << std::endl;
  return 0;
}