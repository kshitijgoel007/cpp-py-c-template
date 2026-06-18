#include "cpp_wrapper.h"

#include <cstdint>
#include <limits>
#include <utility>

#include <gtest/gtest.h>

TEST(CalculatorTest, AddsCheckedIntegers)
{
  Calculator calculator;
  EXPECT_EQ(calculator.add(20, 22), 42);
  EXPECT_THROW(calculator.add(std::numeric_limits<std::int64_t>::max(), 1), std::overflow_error);
}

TEST(AccumulatorTest, OwnsAndMovesTheCoreResource)
{
  Accumulator accumulator(40);
  EXPECT_EQ(accumulator.add(2), 42);

  Accumulator moved(std::move(accumulator));
  EXPECT_EQ(moved.total(), 42);
}

TEST(AccumulatorTest, PreservesStateAfterOverflow)
{
  const auto maximum = std::numeric_limits<std::int64_t>::max();
  Accumulator accumulator(maximum);
  EXPECT_THROW(accumulator.add(1), std::overflow_error);
  EXPECT_EQ(accumulator.total(), maximum);
}
