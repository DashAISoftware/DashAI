from typing import List, Type


def list_field(t: type) -> Type[List]:
    """Function to create a pydantic-like list type.

    Returns
    -------
    List[t]
        A pydantic-like type to represent a list of elements of "t" type.
    """
    return List[t]
