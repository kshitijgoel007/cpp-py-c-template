python := if os_family() == "windows" { ".venv/Scripts/python.exe" } else { ".venv/bin/python" }
exe_suffix := if os_family() == "windows" { ".exe" } else { "" }

# Show the available workflows.
default:
    @just --list

# Create the Python 3.14 environment exclusively with virtualenv.
env:
    #!/usr/bin/env sh
    set -eu
    if [ ! -x "{{ python }}" ]; then
        command -v virtualenv >/dev/null 2>&1 || {
            echo "virtualenv is required and was not found on PATH." >&2
            exit 1
        }
        virtualenv --python 3.14 .venv
    fi
    if [ ! -f .venv/.template-ready-v2 ]; then
        {{ python }} -m pip install --upgrade virtualenv "setuptools>=61.0" wheel
        {{ python }} -m pip install --no-build-isolation --editable ".[dev]"
        touch .venv/.template-ready-v2
    fi

# Configure and build a CMake preset: dev, release, asan, or coverage.
build preset="dev":
    cmake --preset {{ preset }}
    cmake --build --preset {{ preset }}

# Extract the C API and generate the low-level Python ctypes binding.
bindings: env
    {{ python }} tools/bindings/extract_api.py
    {{ python }} tools/bindings/generate_ctypes.py

# Run CTest, pytest, and both consumer demos.
test: build bindings
    ctest --preset dev
    PYTHONPATH=src {{ python }} -m pytest
    ./build/dev/bin/cpp_demo{{ exe_suffix }}
    PYTHONPATH=src {{ python }} main.py

# Run format, static-analysis, generation, ABI, policy, and test checks.
check: test
    {{ python }} tools/bindings/generate_ctypes.py --check
    {{ python }} tools/bindings/generate_abi.py
    {{ python }} tools/bindings/validate_abi.py
    {{ python }} tools/check_environment_policy.py
    {{ python }} -m ruff format --check .
    {{ python }} -m ruff check .
    clang-format --dry-run --Werror c_lib/*.c c_lib/*.h cpp_wrapper/*.cpp cpp_wrapper/*.h tests/c/*.c tests/cpp/*.cpp
    git diff --check

# Format Python and native sources.
format: env
    {{ python }} -m ruff format .
    {{ python }} -m ruff check --fix .
    clang-format -i c_lib/*.c c_lib/*.h cpp_wrapper/*.cpp cpp_wrapper/*.h tests/c/*.c tests/cpp/*.cpp

# Run Python coverage and produce native coverage instrumentation.
coverage: env bindings
    cmake --preset coverage
    cmake --build --preset coverage
    ctest --preset coverage
    PYTHONPATH=src {{ python }} -m pytest --cov --cov-report=term-missing --cov-report=xml

# Run the sanitizer-enabled native suite.
sanitize:
    cmake --preset asan
    cmake --build --preset asan
    ctest --preset asan

# Build a platform-tagged Python wheel in dist/.
wheel: env
    {{ python }} -m pip wheel --no-build-isolation --no-deps . -w dist

# Test clean editable and wheel installations outside the repository.
package-smoke mode="all": env
    {{ python }} tools/bindings/package_smoke.py {{ mode }}

# Install the C and C++ SDK under a user-writable prefix.
install-cpp prefix="build/install": (build "release")
    #!/usr/bin/env sh
    set -eu
    case "{{ prefix }}" in
        /|/bin|/etc|/lib|/opt|/sbin|/System|/usr|/var|/bin/*|/etc/*|/lib/*|/opt/*|/sbin/*|/System/*|/usr/*|/var/*)
            echo "Refusing system install prefix: {{ prefix }}" >&2
            echo "Choose a user-writable path; privileged installation is prohibited." >&2
            exit 1
            ;;
    esac
    cmake --install build/release --prefix {{ prefix }}

# Validate Copier customization in a temporary output directory.
template-smoke: env
    {{ python }} tools/template_smoke.py

# Remove generated environments, builds, packages, and caches.
clean:
    rm -rf build dist .venv .pytest_cache .ruff_cache htmlcov coverage.xml
    rm -rf src/my_c_wrapper/lib src/my_c_wrapper.egg-info
    rm -f src/my_c_wrapper/_ctypes.py
    find . -type d \( -name __pycache__ -o -name "*.egg-info" \) -exec rm -rf {} +
