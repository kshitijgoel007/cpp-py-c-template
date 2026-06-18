"""PEP 517 backend that builds, bundles, and platform-tags the C library."""

import base64
import csv
import hashlib
import io
import subprocess
import sys
import sysconfig
import zipfile
from pathlib import Path

from setuptools import build_meta as _setuptools

ROOT = Path(__file__).resolve().parents[2]
NATIVE_BUILD = ROOT / "build" / "native-wheel"


def _require_virtualenv():
    if sys.prefix == sys.base_prefix:
        raise RuntimeError(
            "The native build backend must run inside an environment created by virtualenv."
        )


def _run(command):
    subprocess.run(command, cwd=ROOT, check=True)


def _prepare_native():
    _require_virtualenv()
    _run(
        [
            "cmake",
            "-S",
            ".",
            "-B",
            str(NATIVE_BUILD),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_TESTING=OFF",
            "-DMYPROJECT_BUILD_CPP=OFF",
            "-DMYPROJECT_BUILD_EXAMPLES=OFF",
        ]
    )
    _run(["cmake", "--build", str(NATIVE_BUILD), "--config", "Release", "--target", "c_lib"])
    _run([sys.executable, "tools/bindings/extract_api.py"])
    _run([sys.executable, "tools/bindings/generate_ctypes.py"])


def _platform_tag():
    return sysconfig.get_platform().replace("-", "_").replace(".", "_")


def _digest(data):
    value = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    return f"sha256={value.decode()}"


def _retag_wheel(path):
    platform_tag = _platform_tag()
    parts = path.stem.split("-")
    if len(parts) < 5:
        raise RuntimeError(f"unexpected wheel filename: {path.name}")
    new_name = "-".join([*parts[:-3], "py3", "none", platform_tag]) + ".whl"
    destination = path.with_name(new_name)

    with zipfile.ZipFile(path) as source:
        files = {name: source.read(name) for name in source.namelist()}
    wheel_name = next(name for name in files if name.endswith(".dist-info/WHEEL"))
    record_name = next(name for name in files if name.endswith(".dist-info/RECORD"))
    wheel_text = files[wheel_name].decode()
    lines = []
    for line in wheel_text.splitlines():
        if line.startswith("Root-Is-Purelib:"):
            line = "Root-Is-Purelib: false"
        elif line.startswith("Tag:"):
            line = f"Tag: py3-none-{platform_tag}"
        lines.append(line)
    files[wheel_name] = ("\n".join(lines) + "\n").encode()

    rows = []
    for name, data in sorted(files.items()):
        if name == record_name:
            continue
        rows.append((name, _digest(data), str(len(data))))
    rows.append((record_name, "", ""))
    output = io.StringIO()
    csv.writer(output, lineterminator="\n").writerows(rows)
    files[record_name] = output.getvalue().encode()

    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name, data in files.items():
            target.writestr(name, data)
    path.unlink()
    return destination


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """Build a wheel containing the platform-native C library."""

    _prepare_native()
    filename = _setuptools.build_wheel(wheel_directory, config_settings, metadata_directory)
    wheel = Path(wheel_directory) / filename
    return _retag_wheel(wheel).name


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    """Build an editable installation after preparing native artifacts."""

    _prepare_native()
    return _setuptools.build_editable(wheel_directory, config_settings, metadata_directory)


def build_sdist(sdist_directory, config_settings=None):
    """Build a source distribution through setuptools."""

    return _setuptools.build_sdist(sdist_directory, config_settings)


def get_requires_for_build_wheel(config_settings=None):
    return _setuptools.get_requires_for_build_wheel(config_settings)


def get_requires_for_build_editable(config_settings=None):
    return _setuptools.get_requires_for_build_editable(config_settings)


def get_requires_for_build_sdist(config_settings=None):
    return _setuptools.get_requires_for_build_sdist(config_settings)


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    return _setuptools.prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    return _setuptools.prepare_metadata_for_build_editable(metadata_directory, config_settings)
