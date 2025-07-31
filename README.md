# Template for C++ and Python Layers over a Core C Library

This is a minimal, self-contained template project demonstrating how to build independent C++ and Python layers on top of a single, shared C library.

- The **C++ layer** provides an object-oriented C++ wrapper (`Calculator` class) for use in other C++ applications. It can be installed system-wide via standard CMake commands.
- The **Python layer** provides a standard, installable Python package that exposes the C library's functionality directly to Python. It uses `ctypes` with auto-generated stubs for a modern IDE experience.

The project has **zero runtime dependencies** and uses standard CMake and Setuptools.

## Project Structure

```txt
.
├── src/
│   └── my_c_wrapper/       # The source for the Python package layer
│       ├── __init__.py
│       ├── lib/              # The compiled C library is copied here for packaging
│       ├── stubs.py          # Auto-generated stubs for the C library
│       └── wrapper.py        # High-level Python wrapper over the C library
├── c_lib/                  # The shared, core C library
├── cpp_wrapper/            # A C++ wrapper (static library) for use by C++ applications
├── main.cpp                # Demonstrates consuming the C++ layer
├── main.py                 # Demonstrates consuming the Python layer
├── CMakeLists.txt          # Build script for both C++ and Python workflows
├── justfile                # Automation script for common tasks
├── MANIFEST.in             # Config file telling setuptools which non-Python files to include
├── pyproject.toml          # Python packaging configuration
└── .gitignore
```

## Using the `justfile` (Recommended Workflow)

This project includes a `justfile` to automate common development tasks. `just` is a modern command runner that provides a simpler alternative to `make`.

### 1. Install `just`

If you don't have it, you'll need to install it once.

**On macOS (using Homebrew):**

```bash
brew install just
```

**On other systems:**
Follow the installation instructions in the [official `just` repository](https://github.com/casey/just).

### 2. Common Commands

Run these from the project's root directory.

- **List all available commands:**

  ```bash
  just --list
  ```

- **Build all C/C++ components:**

  ```bash
  just build
  ```

- **Prepare the entire project for Python packaging (builds C++ and generates stubs):**

  ```bash
  just prepare-python
  ```

- **Run the C++ demo:**

  ```bash
  just test-cpp
  ```

- **Run the Python demo (after `pip install .`):**

  ```bash
  just test-py
  ```

- **Install C++ libraries to the system (e.g., /usr/local):**

  ```bash
  just install-cpp
  ```

- **Uninstall C++ libraries from the system:**

  ```bash
  just uninstall-cpp
  ```

- **Uninstall the Python package from your Python environment:**

  ```bash
  just uninstall-py
  ```

- **Clean up all local generated files and directories:**

  ```bash
  just clean
  ```

---

## Manual Workflow 1: Using the C++ Layer

This workflow builds and installs the C and C++ libraries so other C++ projects can find and link against them.

### 1. Prerequisites

- A C++ compiler (GCC or Clang)
- CMake (version 3.12+)

### 2. Build and Install

```bash
# Configure the build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release

# Build the libraries and the C++ demo executable
cmake --build build

# (Optional) Run the C++ demo to test the wrapper
./build/bin/cpp_demo

# Install headers and libraries to a system path (e.g., /usr/local)
# You may need sudo for this step. If you wish to install locally instead,
# please refer to CMake docs.
sudo cmake --install build
```

This installs the shared library `libc_lib.so`, the static library `libcpp_wrapper.a`, and places the public headers into a namespaced directory (e.g., `/usr/local/include/my_project/`) for other C++ projects to consume.

---

## Manual Workflow 2: Using the Python Layer

This workflow builds a self-contained Python package that bundles the required C library. It does **not** require a system-wide C++ installation.

### 1. Prerequisites

- A C++ compiler, CMake (3.12+), Python 3
- `ctypesgen` (install once for development: `pip install ctypesgen`)

### 2. Build C Library & Prepare Python Source Tree

This command compiles the core C library and automatically copies it into the Python source directory (`src/my_c_wrapper/lib/`).

```bash
cmake -S . -B build
cmake --build build
```

### 3. Generate Python Stubs

This command parses the C header and generates the low-level `stubs.py` file. The `-L` flag (to add a library search path) and the `--library` flag (to specify which library to load) are both crucial for the stubs to work correctly.

```bash
ctypesgen c_lib/c_lib.h -L ./build/lib --library c_lib -o src/my_c_wrapper/stubs.py
```

> **Note:** You may see harmless `ERROR: ... Syntax error` messages. As long as the command finishes with "Wrapping complete", it has succeeded. If you encounter other problems after this, consider going through ongoing issues in ctypesgen repository.

### 4. Install the Python Package

Build and install the Python package using `pip`. This command automatically reads `MANIFEST.in` to find and bundle the C library into the final package.

```bash
pip install .
```

### 5. Run the Python Demo

Now you can use the installed package in any Python script, from any directory.

```bash
python3 main.py
```

Warning: Parts of this code were generated using Gemini 2.5 Pro.
