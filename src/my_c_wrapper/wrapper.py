"""Pythonic wrappers over the generated low-level ctypes API."""

import ctypes

from . import _ctypes


def abi_version():
    """Return the ABI version of the loaded C library."""

    return _ctypes.core_abi_version()


def version():
    """Return the semantic version of the loaded C library."""

    value = _ctypes.core_version_string()
    if value is None:
        raise RuntimeError("the C library returned no version string")
    return value.decode("utf8")


def _checked_integer(value, *, bits, name):
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1
    if not minimum <= value <= maximum:
        raise OverflowError(f"{name} does not fit in a signed {bits}-bit integer")
    return value


def add(a, b):
    """Return the sum of two integers."""

    result = ctypes.c_int64()
    status = _ctypes.checked_add(
        _checked_integer(a, bits=64, name="a"),
        _checked_integer(b, bits=64, name="b"),
        ctypes.byref(result),
    )
    if status == _ctypes.C_CORE_OVERFLOW:
        raise OverflowError("sum would overflow int64")
    if status != _ctypes.C_CORE_OK:
        raise RuntimeError("the C library rejected the addition")
    return result.value


class Accumulator:
    """Own a stateful accumulator implemented by the C library."""

    def __init__(self, initial_value=0):
        self._handle = None
        self._handle = _ctypes.accumulator_create(
            _checked_integer(initial_value, bits=64, name="initial_value")
        )
        if not self._handle:
            raise MemoryError("the C library could not allocate an accumulator")

    @property
    def closed(self):
        """Return whether the underlying C resource has been released."""

        return self._handle is None

    def _require_open(self):
        if self._handle is None:
            raise RuntimeError("accumulator is closed")
        return self._handle

    def add(self, value):
        """Add a value and return the updated total."""

        total = ctypes.c_int64()
        status = _ctypes.accumulator_add(
            self._require_open(),
            _checked_integer(value, bits=64, name="value"),
            ctypes.byref(total),
        )
        if status == _ctypes.C_CORE_OVERFLOW:
            raise OverflowError("accumulator total would overflow int64")
        if status != _ctypes.C_CORE_OK:
            raise RuntimeError("the C library rejected the accumulator update")
        return total.value

    @property
    def total(self):
        """Return the current total."""

        total = ctypes.c_int64()
        status = _ctypes.accumulator_total(self._require_open(), ctypes.byref(total))
        if status != _ctypes.C_CORE_OK:
            raise RuntimeError("the C library could not read the accumulator")
        return total.value

    def close(self):
        """Release the owned C resource. Calling this twice is safe."""

        if self._handle is not None:
            _ctypes.accumulator_destroy(self._handle)
            self._handle = None

    def __enter__(self):
        self._require_open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        self.close()
