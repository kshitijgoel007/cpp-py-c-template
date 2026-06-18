"""Compile and run a C probe that records ABI sizes, alignments, and offsets."""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from common import (
    ABI_JSON_PATH,
    API_JSON_PATH,
    POLICY_PATH,
    ROOT,
    load_policy,
    policy_headers,
    require_virtualenv,
)


def _source(api, policy):
    records = {record["name"]: record for record in api.get("records", [])}
    selected_records = policy.get("abi", {}).get("records", [])
    scalars = policy.get("abi", {}).get("scalars", [])
    lines = ["#include <stddef.h>", "#include <stdio.h>"]
    lines.extend(
        f'#include "{path.relative_to(ROOT).as_posix()}"' for path in policy_headers(policy)
    )
    lines.extend(
        [
            "#define EMIT_TYPE(name, type) \\",
            '    printf("%s\\"" name "\\":{\\"size\\":%zu,\\"align\\":%zu}", \\',
            '           first ? "" : ",", sizeof(type), _Alignof(type)); first = 0',
            "int main(void)",
            "{",
            "    int first = 1;",
            '    printf("{\\"types\\":{");',
        ]
    )
    for index, scalar in enumerate(scalars):
        lines.append(f'    EMIT_TYPE("scalar_{index}", {scalar});')
    lines.extend(['    printf("},\\"records\\":{");', "    first = 1;"])
    for record_name in selected_records:
        record = records.get(record_name)
        if record is None:
            raise RuntimeError(f"ABI policy names missing record: {record_name}")
        lines.append(
            f'    printf("%s\\"{record_name}\\":{{\\"size\\":%zu,\\"align\\":%zu,'
            '\\"fields\\":{", first ? "" : ",", '
            f"sizeof({record_name}), _Alignof({record_name}));"
        )
        lines.append("    first = 0;")
        lines.append("    int first_field = 1;")
        for field in record["fields"]:
            lines.append(
                f'    printf("%s\\"{field["name"]}\\":%zu", first_field ? "" : ",", '
                f"offsetof({record_name}, {field['name']}));"
            )
            lines.append("    first_field = 0;")
        lines.append('    printf("}}");')
    lines.extend(['    printf("}}\\n");', "    return 0;", "}"])
    return "\n".join(lines) + "\n"


def main():
    require_virtualenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", type=Path, default=API_JSON_PATH)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--output", type=Path, default=ABI_JSON_PATH)
    parser.add_argument("--cc", default="cc")
    args = parser.parse_args()

    api = json.loads(args.api.read_text())
    policy = load_policy(args.policy)
    source = _source(api, policy)
    with tempfile.TemporaryDirectory(prefix="my-c-wrapper-abi-") as directory:
        root = Path(directory)
        source_path = root / "probe.c"
        executable = root / "probe"
        source_path.write_text(source)
        subprocess.run(
            [args.cc, "-std=c11", "-I", str(ROOT), str(source_path), "-o", str(executable)],
            check=True,
            cwd=ROOT,
        )
        result = subprocess.run(
            [str(executable)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            cwd=ROOT,
        )
    facts = json.loads(result.stdout)
    facts["schema_version"] = 1
    facts["scalar_names"] = policy.get("abi", {}).get("scalars", [])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
