from typing import Tuple

def foo() -> Tuple[str, str]:
    """
    This function demonstrates the use of type hints in Python.
    It returns a tuple containing two strings.

    Returns:
        tuple[str, str]: A tuple containing two strings.
    """
    return ("foo", "bar")

print(foo())