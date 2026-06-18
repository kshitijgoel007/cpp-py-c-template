# Contributing

## Environment

`sudo` is prohibited. All Python commands must run in `.venv`, created by
`virtualenv` through:

```bash
just env
```

Python 3.14 is the default development version.

## Development Loop

```bash
just format
just check
just package-smoke wheel
```

Native tests use CTest with a pure-C executable and GoogleTest. Python tests
use pytest. Add tests at the layer where behavior is owned, and add
cross-language tests when changing the C ABI.

## Pull Requests

- Keep generated files out of commits.
- Document public API and ABI changes in `CHANGELOG.md`.
- Preserve unrelated user changes.
- Verify the exported CMake consumer and installed Python wheel.
- Do not introduce privileged installation steps.

