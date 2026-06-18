"""Runtime enforcement for the package's virtualenv-only policy."""

import sys


def require_virtualenv():
    """Reject imports from a system Python interpreter."""

    if sys.prefix == sys.base_prefix:
        raise RuntimeError(
            "my_c_wrapper must run inside an environment created by virtualenv. "
            "Create one with `virtualenv .venv` and use that environment's Python."
        )
