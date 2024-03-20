from typing import Type


def bool_field() -> Type[bool]:
    """Function to create a pydantic-like boolean type.

    Returns
    -------
    type[bool]
        A pydantic-like type to represent the boolean.
    """
    return bool
