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
# This recipe requires sudo permissions.
install-cpp: build
    @echo "--- Installing C++ libraries and headers (requires sudo)... ---"
    @sudo cmake --install {{BUILD_DIR}}
    @echo "Installation complete."

# [Workflow 2] Prepare the project for Python packaging.
# This is a convenient alias that runs the necessary build steps.
prepare-python: stubs
    @echo "\nPython package is ready."
    @echo "To install, run: pip install ."

# --- Cleanup ---

# Remove all generated files and build artifacts.
clean:
    @echo "--- Cleaning project... ---"
    @rm -rf {{BUILD_DIR}}
    @rm -rf dist
    @rm -rf {{PYTHON_LIB_DIR}}
    @rm -f {{STUB_FILE}}
    @echo "Finding and removing generated Python directories (__pycache__, *.egg-info)..."
    @find . -type d \( -name "__pycache__" -o -name "*.egg-info" \) -exec rm -rf {} +
    @echo "Cleanup complete."
