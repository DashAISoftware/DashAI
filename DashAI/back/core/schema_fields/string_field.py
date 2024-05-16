from typing import Type


def string_field() -> Type[str]:
    """Function to create a pydantic-like string type.
    The created type will accept any string given by the user.

    Returns
    -------
    type[str]
        A pydantic-like type to represent a raw string.
    """
    return str
