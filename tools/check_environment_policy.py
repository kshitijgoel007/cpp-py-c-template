"""Enforce repository rules for privilege and Python environment usage."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTOMATION_FILES = [
    ROOT / "justfile",
    ROOT / "CMakeLists.txt",
    *sorted((ROOT / "tools").rglob("*.py")),
]
INSTRUCTION_FILES = [
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    *sorted(ROOT.rglob("AGENTS.md")),
    *sorted((ROOT / "docs").glob("*.md")),
]


def _require_virtualenv():
    if sys.prefix == sys.base_prefix:
        return ["policy check must run inside a virtualenv-created environment"]
    return []


def _check_automation():
    errors = []
    command_pattern = re.compile(r"(^|[;&|]\s*)sudo(?:\s|$)", re.MULTILINE)
    for path in AUTOMATION_FILES:
        text = path.read_text()
        if command_pattern.search(text):
            errors.append(f"{path.relative_to(ROOT)} contains a sudo command")

    package_smoke = (ROOT / "tools" / "bindings" / "package_smoke.py").read_text()
    if re.search(r"^\s*import venv\s*$", package_smoke, re.MULTILINE):
        errors.append("package_smoke.py must use virtualenv, not stdlib venv")

    justfile = (ROOT / "justfile").read_text()
    if '".venv/bin/python"' not in justfile:
        errors.append("justfile Python commands must use .venv/bin/python")
    if "Refusing system install prefix" not in justfile:
        errors.append("justfile must reject system C++ install prefixes")
    package_init = (ROOT / "src" / "my_c_wrapper" / "__init__.py").read_text()
    if "require_virtualenv()" not in package_init:
        errors.append("Python package must enforce virtualenv usage at import time")
    for path in (ROOT / "tools").rglob("*.py"):
        if path.read_text().startswith("#!/usr/bin/env python"):
            errors.append(f"{path.relative_to(ROOT)} has a system-Python shebang")
    return errors


def _check_instructions():
    errors = []
    for path in INSTRUCTION_FILES:
        text = path.read_text().lower()
        if path.name.lower() == "agents.md" and "sudo is prohibited" not in text.replace("`", ""):
            errors.append(f"{path.relative_to(ROOT)} must state that sudo is prohibited")
        if path in (ROOT / "README.md", ROOT / "AGENTS.md"):
            if "virtualenv" not in text:
                errors.append(f"{path.relative_to(ROOT)} must require virtualenv")
    return errors


def main():
    errors = [*_require_virtualenv(), *_check_automation(), *_check_instructions()]
    if errors:
        raise SystemExit("environment policy failed:\n- " + "\n- ".join(errors))
    print("environment policy passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
