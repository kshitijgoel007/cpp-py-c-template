"""Shared helpers for the C-to-Python binding pipeline."""

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "bindings" / "bindings.toml"
API_JSON_PATH = ROOT / "build" / "bindings" / "api.json"
ABI_JSON_PATH = ROOT / "build" / "bindings" / "abi.json"
GENERATED_BINDING_PATH = ROOT / "src" / "my_c_wrapper" / "_ctypes.py"


def require_virtualenv():
    """Reject project Python execution outside a virtualenv environment."""

    if sys.prefix == sys.base_prefix:
        raise RuntimeError(
            "Python project commands must run inside an environment created by virtualenv. "
            "Run `just env` first."
        )


def load_policy(path=POLICY_PATH):
    """Load the source-controlled binding policy."""

    with path.open("rb") as file:
        return tomllib.load(file)


def policy_headers(policy):
    """Return policy headers as absolute paths."""

    return [ROOT / value for value in policy.get("headers", {}).get("include", [])]
