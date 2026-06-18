"""Apply Copier answers to the copied starter project."""

import argparse
import sys
from pathlib import Path

ROOT = Path.cwd()
TEXT_SUFFIXES = {
    "",
    ".c",
    ".cc",
    ".cmake",
    ".cpp",
    ".h",
    ".in",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}
SKIP_PARTS = {".git", ".venv", "build", "dist", "__pycache__"}


def _require_virtualenv():
    if sys.prefix == sys.base_prefix:
        raise RuntimeError("Copier customization must run inside virtualenv")


def _text_files():
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or SKIP_PARTS.intersection(path.parts):
            continue
        if path == Path(__file__).resolve():
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in {"justfile", ".gitignore"}:
            files.append(path)
    return files


def _replace_text(replacements):
    for path in _text_files():
        text = path.read_text()
        updated = text
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated)


def _rename_path(source, destination):
    if source == destination:
        return
    if destination.exists():
        raise RuntimeError(f"customization destination already exists: {destination}")
    source.rename(destination)


def main():
    _require_virtualenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--cmake-name", required=True)
    parser.add_argument("--project-slug", required=True)
    parser.add_argument("--distribution-name", required=True)
    parser.add_argument("--python-package", required=True)
    parser.add_argument("--author-name", required=True)
    parser.add_argument("--author-email", required=True)
    args = parser.parse_args()

    replacements = {
        "My Project": args.project_name,
        "MyProject": args.cmake_name,
        "my_project": args.project_slug,
        "my-c-wrapper": args.distribution_name,
        "my_c_wrapper": args.python_package,
        "Your Name": args.author_name,
        "your@email.com": args.author_email,
    }
    _replace_text(replacements)

    _rename_path(
        ROOT / "src" / "my_c_wrapper",
        ROOT / "src" / args.python_package,
    )
    _rename_path(
        ROOT / "cmake" / "MyProjectConfig.cmake.in",
        ROOT / "cmake" / f"{args.cmake_name}Config.cmake.in",
    )

    pyproject = (ROOT / "pyproject.toml").read_text()
    if f'name = "{args.distribution_name}"' not in pyproject:
        raise RuntimeError("distribution name customization failed")
    if not (ROOT / "src" / args.python_package / "__init__.py").exists():
        raise RuntimeError("Python package customization failed")

    print(f"Customized template as {args.project_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
