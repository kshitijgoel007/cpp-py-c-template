"""Tests for the supported Python wrapper API."""

import sys

import pytest

from my_c_wrapper import Accumulator, abi_version, add, version


def test_loaded_library_version_matches_package():
    assert version() == "2026.6.1"
    assert abi_version() == 1


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [(7, 5, 12), (-7, 5, -2), (0, 0, 0)],
)
def test_add(left, right, expected):
    assert add(left, right) == expected


def test_add_rejects_non_integer_and_out_of_range_values():
    with pytest.raises(TypeError):
        add("7", 5)
    with pytest.raises(OverflowError):
        add(1 << 63, 0)
    with pytest.raises(OverflowError):
        add((1 << 63) - 1, 1)


def test_accumulator_keeps_state_in_the_c_library():
    accumulator = Accumulator(10)
    assert accumulator.total == 10
    assert accumulator.add(5) == 15
    assert accumulator.add(-3) == 12
    assert accumulator.total == 12
    accumulator.close()


def test_accumulator_context_manager_closes_the_resource():
    with Accumulator(4) as accumulator:
        assert accumulator.add(6) == 10
        assert not accumulator.closed
    assert accumulator.closed


def test_accumulator_overflow_preserves_state():
    maximum = (1 << 63) - 1
    with Accumulator(maximum) as accumulator:
        with pytest.raises(OverflowError):
            accumulator.add(1)
        assert accumulator.total == maximum


def test_accumulator_close_is_idempotent():
    accumulator = Accumulator()
    accumulator.close()
    accumulator.close()
    with pytest.raises(RuntimeError, match="closed"):
        accumulator.add(1)
    with pytest.raises(RuntimeError, match="closed"):
        _ = accumulator.total


def test_accumulator_validates_int64_range():
    with pytest.raises(OverflowError):
        Accumulator(1 << 63)
    with Accumulator() as accumulator:
        with pytest.raises(OverflowError):
            accumulator.add(1 << 63)


def test_loader_env_override_missing_file_falls_through(monkeypatch, tmp_path):
    """MY_C_WRAPPER_LIBRARY pointing to a missing file falls through to other candidates."""
    monkeypatch.setenv("MY_C_WRAPPER_LIBRARY", str(tmp_path / "nonexistent.so"))
    from my_c_wrapper._loader import load_library

    lib = load_library()
    assert lib is not None


def test_loader_raises_when_no_candidate_found(monkeypatch):
    """load_library raises RuntimeError when all candidate paths are missing."""
    from my_c_wrapper import _loader

    monkeypatch.setattr(_loader, "LIBRARY_NAMES", {"_never_": ("no_such_lib.so",)})
    monkeypatch.delenv("MY_C_WRAPPER_LIBRARY", raising=False)
    with pytest.raises(RuntimeError, match="Unable to load"):
        _loader.load_library()


def test_environment_raises_outside_virtualenv(monkeypatch):
    """require_virtualenv raises when sys.prefix matches the base prefix."""
    monkeypatch.setattr(sys, "prefix", sys.base_prefix)
    from my_c_wrapper._environment import require_virtualenv

    with pytest.raises(RuntimeError, match="virtualenv"):
        require_virtualenv()
