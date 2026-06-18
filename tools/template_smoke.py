"""Render the Copier template with non-default names and validate the result."""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.prefix == sys.base_prefix:
        raise RuntimeError("template smoke must run inside virtualenv")

    with tempfile.TemporaryDirectory(prefix="cpp-py-c-template-") as directory:
        destination = Path(directory) / "vector-engine"
        command = [
            sys.executable,
            "-m",
            "copier",
            "copy",
            "--trust",
            "--defaults",
            "--data",
            "project_name=Vector Engine",
            "--data",
            "cmake_name=VectorEngine",
            "--data",
            "project_slug=vector_engine",
            "--data",
            "distribution_name=vector-engine",
            "--data",
            "python_package=vector_engine",
            "--data",
            "author_name=Template Test",
            "--data",
            "author_email=template@example.com",
            str(ROOT),
            str(destination),
        ]
        subprocess.run(command, cwd=ROOT, check=True)

        pyproject = (destination / "pyproject.toml").read_text()
        cmake = (destination / "CMakeLists.txt").read_text()
        assert 'name = "vector-engine"' in pyproject
        assert "project(VectorEngine" in cmake
        assert (destination / "src" / "vector_engine" / "__init__.py").exists()
        assert (destination / "cmake" / "VectorEngineConfig.cmake.in").exists()

    print("Copier template smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
