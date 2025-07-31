#include "cpp_wrapper.h"
#include <iostream>

extern "C" {
#include "c_lib.h"
}

Calculator::Calculator()
{
  std::cout << "[C++] Calculator object created." << std::endl;
}

int Calculator::add(int a, int b)
{
  std::cout << "[C++] Calling C function from C++ layer." << std::endl;
  return add_integers(a, b);
}