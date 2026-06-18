"""Validate generated ctypes layouts against compiler-derived C ABI facts."""

import argparse
import ctypes
import importlib
import json
import os
import sys
from pathlib import Path

from common import ABI_JSON_PATH, ROOT, require_virtualenv

SCALAR_CTYPES = {
    "int": ctypes.c_int,
    "void *": ctypes.c_void_p,
}


def main():
    require_virtualenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abi", type=Path, default=ABI_JSON_PATH)
    parser.add_argument("--library", type=Path)
    args = parser.parse_args()

    if args.library:
        os.environ["MY_C_WRAPPER_LIBRARY"] = str(args.library.resolve())
    sys.path.insert(0, str(ROOT / "src"))
    generated = importlib.import_module("my_c_wrapper._ctypes")
    facts = json.loads(args.abi.read_text())
    errors = []

    for index, name in enumerate(facts.get("scalar_names", [])):
        ctype = SCALAR_CTYPES.get(name)
        if ctype is None:
            errors.append(f"no ctypes validator mapping for scalar {name!r}")
            continue
        fact = facts["types"][f"scalar_{index}"]
        if ctypes.sizeof(ctype) != fact["size"]:
            errors.append(f"{name}: size {ctypes.sizeof(ctype)} != {fact['size']}")
        if ctypes.alignment(ctype) != fact["align"]:
            errors.append(f"{name}: alignment {ctypes.alignment(ctype)} != {fact['align']}")

    for name, fact in facts.get("records", {}).items():
        ctype = getattr(generated, name)
        if ctypes.sizeof(ctype) != fact["size"]:
            errors.append(f"{name}: size {ctypes.sizeof(ctype)} != {fact['size']}")
        if ctypes.alignment(ctype) != fact["align"]:
            errors.append(f"{name}: alignment {ctypes.alignment(ctype)} != {fact['align']}")
        for field, offset in fact["fields"].items():
            actual = getattr(ctype, field).offset
            if actual != offset:
                errors.append(f"{name}.{field}: offset {actual} != {offset}")

    if errors:
        raise SystemExit("ABI validation failed:\n- " + "\n- ".join(errors))
    print("ABI validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
