#include "cpp_wrapper.h"

#include <new>
#include <stdexcept>
#include <utility>

Calculator::Calculator() = default;

std::int64_t Calculator::add(std::int64_t a, std::int64_t b)
{
  std::int64_t result = 0;
  CCoreStatus status = checked_add(a, b, &result);
  if (status == C_CORE_OVERFLOW)
  {
    throw std::overflow_error("sum would overflow int64");
  }
  if (status != C_CORE_OK)
  {
    throw std::runtime_error("cannot add with an invalid output");
  }
  return result;
}

Accumulator::Accumulator(std::int64_t initial_value)
  : accumulator_(accumulator_create(initial_value))
{
  if (accumulator_ == nullptr)
  {
    throw std::bad_alloc();
  }
}

Accumulator::~Accumulator()
{
  accumulator_destroy(accumulator_);
}

Accumulator::Accumulator(Accumulator&& other) noexcept
  : accumulator_(std::exchange(other.accumulator_, nullptr))
{
}

Accumulator& Accumulator::operator=(Accumulator&& other) noexcept
{
  if (this != &other)
  {
    accumulator_destroy(accumulator_);
    accumulator_ = std::exchange(other.accumulator_, nullptr);
  }
  return *this;
}

std::int64_t Accumulator::add(std::int64_t value)
{
  std::int64_t result = 0;
  CCoreStatus status = accumulator_add(accumulator_, value, &result);
  if (status == C_CORE_OVERFLOW)
  {
    throw std::overflow_error("accumulator total would overflow int64");
  }
  if (status != C_CORE_OK)
  {
    throw std::runtime_error("cannot add to an invalid accumulator");
  }
  return result;
}

std::int64_t Accumulator::total() const
{
  std::int64_t result = 0;
  if (accumulator_total(accumulator_, &result) != C_CORE_OK)
  {
    throw std::runtime_error("cannot read an invalid accumulator");
  }
  return result;
}
