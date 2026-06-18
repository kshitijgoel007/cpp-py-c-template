from ._environment import require_virtualenv

require_virtualenv()

from .wrapper import Accumulator, abi_version, add, version  # noqa: E402

__version__ = "0.2.0"

__all__ = ["Accumulator", "abi_version", "add", "version"]
