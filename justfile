# ==============================================================================
# A justfile for building, testing, and cleaning the project.
#
# To see available recipes, run: just --list
# ==============================================================================

# --- Variables ---
BUILD_DIR      := "build"
STUB_FILE      := "src/my_c_wrapper/stubs.py"
PYTHON_LIB_DIR := "src/my_c_wrapper/lib"
PYTHON_EXE     := "python3"
PACKAGE_NAME   := "my_c_wrapper"

# --- Default Recipe ---
# The default recipe runs when you execute `just` with no arguments.
default: list

# --- Main Recipes ---

# List available commands.
list:
    @just --list

# [Workflow 1 & 2] Build all C/C++ libraries and executables.
# This also copies the C shared library to the Python source tree.
build:
    @echo "--- Configuring and building C/C++ components... ---"
    @cmake -S . -B {{BUILD_DIR}}
    @cmake --build {{BUILD_DIR}}

# [Workflow 2] Generate the Python stubs file from C headers.
# This depends on the C library having been built first.
stubs: build
    @echo "--- Generating Python stubs with ctypesgen... ---"
    @ctypesgen c_lib/c_lib.h -L ./{{BUILD_DIR}}/lib --library c_lib -o {{STUB_FILE}}

# [Workflow 1] Run the C++ demo executable.
test-cpp: build
    @echo "--- Running C++ Demo Executable ---"
    @./{{BUILD_DIR}}/bin/cpp_demo

# [Workflow 2] Run the Python demo script.
# This assumes the user has already run `pip install .` as per the README.
test-py:
    @echo "--- Running Python Demo (requires 'pip install .') ---"
    @{{PYTHON_EXE}} main.py

# [Workflow 1] Install the C++ libraries and headers system-wide.
install-cpp: build
    @echo "--- Installing C++ libraries and headers (requires sudo)... ---"
    @sudo cmake --install {{BUILD_DIR}}
    @echo "Installation complete."

# [Workflow 1] Uninstall the C++ libraries and headers from the system.
uninstall-cpp:
    @echo "--- Uninstalling C++ components from system (requires sudo)... ---"
    @if [ -f {{BUILD_DIR}}/install_manifest.txt ]; then \
        xargs sudo rm -f < {{BUILD_DIR}}/install_manifest.txt; \
        echo "C++ uninstall complete."; \
    else \
        echo "Error: '{{BUILD_DIR}}/install_manifest.txt' not found."; \
        echo "Cannot uninstall. Please run 'just build' and 'just install-cpp' first."; \
    fi

# [Workflow 2] Prepare the project for Python packaging.
# This is a convenient alias that runs the necessary build steps.
prepare-python: stubs
    @echo "\nPython package is ready."
    @echo "To install, run: pip install ."

# [Workflow 2] Uninstall the Python package.
uninstall-py:
    @echo "--- Uninstalling Python package '{{PACKAGE_NAME}}'... ---"
    @{{PYTHON_EXE}} -m pip uninstall -y {{PACKAGE_NAME}}

# --- Cleanup ---

# Remove all generated files and build artifacts from the local directory.
clean:
    @echo "--- Cleaning project... ---"
    @rm -rf {{BUILD_DIR}}
    @rm -rf dist
    @rm -rf {{PYTHON_LIB_DIR}}
    @rm -f {{STUB_FILE}}
    @echo "Finding and removing generated Python directories (__pycache__, *.egg-info)..."
    @find . -type d \( -name "__pycache__" -o -name "*.egg-info" \) -exec rm -rf {} +
    @echo "Cleanup complete."
