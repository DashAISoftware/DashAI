from typing import List, Optional, Type

from pydantic import Field
from typing_extensions import Annotated


def list_field(
    item_type: Type, min_items: Optional[int] = None, max_items: Optional[int] = None
) -> Type[List]:
    """Function to create a pydantic-like list type.

    Returns
    -------
    List[t]
        A pydantic-like type to represent a list of elements of "t" type.
    """
    return Annotated[List[item_type], Field(min_items=min_items, max_items=max_items)]
