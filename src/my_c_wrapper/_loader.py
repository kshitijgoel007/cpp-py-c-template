"""Locate and load the packaged C library."""

import ctypes
import os
import platform
from pathlib import Path

LIBRARY_NAMES = {
    "Linux": ("libc_lib.so",),
    "Darwin": ("libc_lib.dylib",),
    "Windows": ("c_lib.dll", "libc_lib.dll"),
}


def candidate_library_paths():
    """Yield explicit, packaged, and development library candidates."""

    override = os.environ.get("MY_C_WRAPPER_LIBRARY")
    if override:
        yield Path(override).expanduser()

    names = LIBRARY_NAMES.get(platform.system(), ())
    package = Path(__file__).resolve().parent
    repository = package.parents[1]
    for name in names:
        yield package / "lib" / name
        yield package / name
        yield repository / "build" / "lib" / name
        yield repository / "build" / "dev" / "lib" / name
        yield repository / "build" / "release" / "lib" / name
        yield repository / "build" / "native-wheel" / "lib" / name


def load_library():
    """Load the first usable native library and report all failures."""

    attempted = []
    failures = []
    for candidate in candidate_library_paths():
        path = candidate.resolve()
        attempted.append(str(path))
        if not path.is_file():
            continue
        try:
            return ctypes.CDLL(str(path))
        except OSError as error:
            failures.append(f"{path}: {error}")

    details = [f"attempted: {', '.join(attempted) or 'no paths'}"]
    if failures:
        details.append(f"load failures: {'; '.join(failures)}")
    raise RuntimeError(
        "Unable to load the my_c_wrapper native library. "
        "Set MY_C_WRAPPER_LIBRARY to an explicit library path; " + "; ".join(details)
    )
