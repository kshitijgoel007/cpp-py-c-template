#ifndef CPP_WRAPPER_H
#define CPP_WRAPPER_H

#include <cstdint>

extern "C" {
#include "c_lib.h"
}

class Calculator
{
public:
  Calculator();
  std::int64_t add(std::int64_t a, std::int64_t b);
};

class Accumulator
{
public:
  explicit Accumulator(std::int64_t initial_value = 0);
  ~Accumulator();

  Accumulator(const Accumulator&) = delete;
  Accumulator& operator=(const Accumulator&) = delete;
  Accumulator(Accumulator&& other) noexcept;
  Accumulator& operator=(Accumulator&& other) noexcept;

  std::int64_t add(std::int64_t value);
  std::int64_t total() const;

private:
  CAccumulator* accumulator_;
};

#endif  // CPP_WRAPPER_H
