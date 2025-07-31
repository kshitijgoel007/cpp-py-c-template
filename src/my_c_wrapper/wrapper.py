# src/my_c_wrapper/wrapper.py

try:
    # This allows the wrapper to be part of a package
    from . import stubs
except ImportError:
    # This allows the script to be run directly for testing if needed
    import stubs

# --- Public API ---
def add(a: int, b: int) -> int:
    """
    A high-level, type-hinted wrapper for the add_integers function.
    
    This function simply calls the low-level function from the auto-generated
    stub file, which handles all the ctypes details.
    """
    return stubs.add_integers(a, b)