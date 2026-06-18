"""Extract normalized public C API metadata using Clang's JSON AST."""

import argparse
import json
import subprocess
from pathlib import Path

from common import (
    API_JSON_PATH,
    POLICY_PATH,
    ROOT,
    load_policy,
    policy_headers,
    require_virtualenv,
)


def _run_ast(clang, header):
    command = [
        clang,
        "-x",
        "c",
        "-std=c11",
        "-I",
        str(ROOT / "c_lib"),
        "-Xclang",
        "-ast-dump=json",
        "-fsyntax-only",
        str(header),
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def _location(node, header):
    loc = node.get("loc", {})
    path = loc.get("file")
    if path:
        file = Path(path)
        if not file.is_absolute():
            file = ROOT / file
    else:
        file = header
    try:
        display = file.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        display = str(file)
    return {"file": display, "line": loc.get("line"), "column": loc.get("col")}


def _function(node, header):
    signature = node["type"]["qualType"]
    result = signature.split("(", 1)[0].rstrip()
    parameters = []
    for child in node.get("inner", []):
        if child.get("kind") != "ParmVarDecl":
            continue
        parameters.append(
            {
                "name": child.get("name", ""),
                "type": child["type"]["qualType"],
            }
        )
    return {
        "name": node["name"],
        "result": result,
        "parameters": parameters,
        "location": _location(node, header),
    }


def _record(node, header):
    name = node.get("name")
    if not name:
        return None
    fields = []
    for child in node.get("inner", []):
        if child.get("kind") != "FieldDecl":
            continue
        fields.append({"name": child.get("name", ""), "type": child["type"]["qualType"]})
    return {
        "name": name,
        "kind": node.get("tagUsed", "struct"),
        "opaque": not node.get("completeDefinition", False),
        "fields": fields,
        "location": _location(node, header),
    }


def _enum(node, header):
    name = node.get("name")
    if not name:
        return None
    values = []
    for child in node.get("inner", []):
        if child.get("kind") != "EnumConstantDecl":
            continue
        value = child.get("value")
        if value is None:
            for expression in child.get("inner", []):
                if "value" in expression:
                    value = expression["value"]
                    break
        if value is None:
            raise RuntimeError(f"could not extract enum value for {child['name']}")
        values.append({"name": child["name"], "value": int(value)})
    return {
        "name": name,
        "values": values,
        "location": _location(node, header),
    }


def _referenced_record_names(functions):
    """Return record names actually used in included function signatures."""
    names = set()
    for func in functions.values():
        for type_str in [func["result"]] + [p["type"] for p in func.get("parameters", [])]:
            base = type_str.replace("const ", "").replace(" *", "").replace("*", "").strip()
            names.add(base)
    return names


def extract(clang, policy_path):
    """Extract declarations selected by policy."""

    policy = load_policy(policy_path)
    included = set(policy.get("symbols", {}).get("include", []))
    excluded = set(policy.get("symbols", {}).get("exclude", []))
    functions = {}
    records = {}
    enums = {}
    headers = policy_headers(policy)

    for header in headers:
        ast = _run_ast(clang, header)
        expected = header.resolve().relative_to(ROOT).as_posix()
        header_line_count = len(header.read_text().splitlines())
        for node in ast.get("inner", []):
            location = _location(node, header)
            if location["file"] != expected:
                continue
            if (location["line"] or 0) > header_line_count:
                continue
            kind = node.get("kind")
            if kind == "FunctionDecl":
                function = _function(node, header)
                name = function["name"]
                if included and name not in included:
                    continue
                if name not in excluded:
                    functions[name] = function
            elif kind == "RecordDecl":
                record = _record(node, header)
                if record:
                    current = records.get(record["name"])
                    if current is None or (current["opaque"] and not record["opaque"]):
                        records[record["name"]] = record
            elif kind == "EnumDecl":
                enum = _enum(node, header)
                if enum:
                    enums[enum["name"]] = enum

    missing = included - functions.keys()
    if missing:
        raise RuntimeError(f"binding policy names missing C functions: {sorted(missing)}")

    referenced = _referenced_record_names(functions)
    records = {name: r for name, r in records.items() if name in referenced}

    return {
        "schema_version": 1,
        "generator": "tools/bindings/extract_api.py",
        "headers": [path.resolve().relative_to(ROOT).as_posix() for path in headers],
        "functions": sorted(functions.values(), key=lambda item: item["name"]),
        "records": sorted(records.values(), key=lambda item: item["name"]),
        "enums": sorted(enums.values(), key=lambda item: item["name"]),
    }


def main():
    require_virtualenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--output", type=Path, default=API_JSON_PATH)
    args = parser.parse_args()

    api = extract(args.clang, args.policy)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(api, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output} ({len(api['functions'])} functions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
