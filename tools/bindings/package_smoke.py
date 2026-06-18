"""Build and test editable and wheel installs in isolated virtual environments."""

import argparse
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from common import ROOT, require_virtualenv

SMOKE = """
from pathlib import Path
import my_c_wrapper
from my_c_wrapper import _ctypes

assert my_c_wrapper.add(20, 22) == 42
with my_c_wrapper.Accumulator(40) as accumulator:
    assert accumulator.add(2) == 42
    assert accumulator.total == 42
assert Path(_ctypes._lib._name).is_file(), _ctypes._lib._name
print(f"package smoke passed: {_ctypes._lib._name}")
"""


def _run(command, *, cwd=ROOT):
    subprocess.run(command, cwd=cwd, check=True)


def _venv_python(path):
    return path / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def _environment(path):
    _run([sys.executable, "-m", "virtualenv", "--clear", str(path)])
    python = _venv_python(path)
    _run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "setuptools>=61.0",
            "wheel",
        ]
    )
    return python


def _smoke(python, run_dir):
    run_dir.mkdir(parents=True, exist_ok=True)
    _run([str(python), "-c", SMOKE], cwd=run_dir)


def editable_smoke(work):
    python = _environment(work / "editable-venv")
    _run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--no-build-isolation",
            "--no-deps",
            "-e",
            str(ROOT),
        ]
    )
    _smoke(python, work / "editable-run")


def wheel_smoke(work):
    build_python = _environment(work / "wheel-build-venv")
    wheelhouse = work / "wheelhouse"
    wheelhouse.mkdir()
    _run(
        [
            str(build_python),
            "-m",
            "pip",
            "wheel",
            "--no-build-isolation",
            "--no-deps",
            str(ROOT),
            "-w",
            str(wheelhouse),
        ]
    )
    wheels = sorted(wheelhouse.glob("my_c_wrapper-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected one wheel, found {wheels}")
    wheel = wheels[0]
    if wheel.name.endswith("-any.whl"):
        raise RuntimeError(f"native wheel has a pure-Python tag: {wheel.name}")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    if not any(name.startswith("my_c_wrapper/lib/") for name in names):
        raise RuntimeError("wheel does not contain the native library")

    python = _environment(work / "wheel-install-venv")
    _run([str(python), "-m", "pip", "install", "--no-deps", str(wheel)])
    _smoke(python, work / "wheel-run")


def main():
    require_virtualenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("editable", "wheel", "all"), default="all", nargs="?")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="my-c-wrapper-package-smoke-") as directory:
        work = Path(directory)
        if args.mode in ("editable", "all"):
            editable_smoke(work)
        if args.mode in ("wheel", "all"):
            wheel_smoke(work)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
