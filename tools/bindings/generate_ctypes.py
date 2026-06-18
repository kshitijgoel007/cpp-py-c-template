"""Generate the low-level ctypes module from normalized API metadata."""

import argparse
import json
import re
from pathlib import Path

from common import (
    API_JSON_PATH,
    GENERATED_BINDING_PATH,
    POLICY_PATH,
    load_policy,
    require_virtualenv,
)

CTYPE_MAP = {
    "void": "None",
    "_Bool": "ctypes.c_bool",
    "bool": "ctypes.c_bool",
    "char": "ctypes.c_char",
    "signed char": "ctypes.c_int8",
    "unsigned char": "ctypes.c_uint8",
    "short": "ctypes.c_short",
    "unsigned short": "ctypes.c_ushort",
    "int": "ctypes.c_int",
    "unsigned int": "ctypes.c_uint",
    "long": "ctypes.c_long",
    "unsigned long": "ctypes.c_ulong",
    "long long": "ctypes.c_longlong",
    "unsigned long long": "ctypes.c_ulonglong",
    "float": "ctypes.c_float",
    "double": "ctypes.c_double",
    "size_t": "ctypes.c_size_t",
    "int8_t": "ctypes.c_int8",
    "uint8_t": "ctypes.c_uint8",
    "int16_t": "ctypes.c_int16",
    "uint16_t": "ctypes.c_uint16",
    "int32_t": "ctypes.c_int32",
    "uint32_t": "ctypes.c_uint32",
    "int64_t": "ctypes.c_int64",
    "uint64_t": "ctypes.c_uint64",
}
ARRAY_RE = re.compile(r"^(?P<base>.+?)\s*\[(?P<count>\d+)\]$")


def _clean_type(c_type):
    return " ".join(c_type.replace("*", " * ").split())


def _ctype(c_type, records, enums, *, owned_return=False):
    value = _clean_type(c_type)
    array = ARRAY_RE.match(value)
    if array:
        base = _ctype(array.group("base"), records, enums)
        return f"{base} * {array.group('count')}"

    if value.startswith("const "):
        value = value[6:]
    if value.endswith(" *"):
        base = value[:-2].strip()
        if base == "char":
            if owned_return:
                return "ctypes.c_void_p"
            return "ctypes.c_char_p"
        if base == "void":
            return "ctypes.c_void_p"
        if base in records:
            return f"ctypes.POINTER({base})"
        if base in CTYPE_MAP:
            return f"ctypes.POINTER({CTYPE_MAP[base]})"
        raise ValueError(f"unsupported pointer type: {c_type}")
    if value in CTYPE_MAP:
        return CTYPE_MAP[value]
    if value in records:
        return value
    if value in enums:
        return "ctypes.c_int"
    raise ValueError(f"unsupported C type: {c_type}")


def render(api, policy):
    """Render a deterministic ctypes module."""

    records = {record["name"] for record in api.get("records", [])}
    enums = {enum["name"] for enum in api.get("enums", [])}
    ownership = policy.get("ownership", {})
    exported = []
    lines = [
        '"""Generated raw ctypes bindings. Do not edit by hand."""',
        "",
        "import ctypes",
        "",
        "from ._loader import load_library",
        "",
        "_lib = load_library()",
        "",
    ]

    for enum in api.get("enums", []):
        for value in enum["values"]:
            lines.append(f"{value['name']} = {value['value']}")
            exported.append(value["name"])
        if enum["values"]:
            lines.append("")

    for record in api.get("records", []):
        base = "ctypes.Union" if record["kind"] == "union" else "ctypes.Structure"
        lines.extend([f"class {record['name']}({base}):", "    pass", ""])
        exported.append(record["name"])

    for record in api.get("records", []):
        if record["opaque"] or not record["fields"]:
            continue
        lines.append(f"{record['name']}._fields_ = [")
        for field in record["fields"]:
            field_type = _ctype(field["type"], records, enums)
            lines.append(f"    ({field['name']!r}, {field_type}),")
        lines.extend(["]", ""])

    for function in api.get("functions", []):
        name = function["name"]
        result = _ctype(
            function["result"],
            records,
            enums,
            owned_return=str(ownership.get(name, "")).startswith("owned"),
        )
        args = [
            _ctype(parameter["type"], records, enums)
            for parameter in function.get("parameters", [])
        ]
        lines.extend(
            [
                f"{name} = _lib.{name}",
                f"{name}.restype = {result}",
                f"{name}.argtypes = [{', '.join(args)}]",
                "",
            ]
        )
        exported.append(name)

    lines.extend(
        [
            f"__all__ = {exported!r}",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    require_virtualenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=API_JSON_PATH)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--output", type=Path, default=GENERATED_BINDING_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    api = json.loads(args.input.read_text())
    generated = render(api, load_policy(args.policy))
    if args.check:
        current = args.output.read_text() if args.output.exists() else ""
        if current != generated:
            raise SystemExit(f"{args.output} is stale; run the binding generator")
        print(f"{args.output} is current")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generated)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
