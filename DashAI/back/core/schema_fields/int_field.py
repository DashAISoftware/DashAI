from typing import Optional

from pydantic import Field
from typing_extensions import Annotated


def int_field(
    description: str,
    default: int,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
):
    params = {"description": description, "default": default}
    if minimum:
        params["ge"] = minimum
    if maximum:
        params["le"] = maximum
    return Annotated[
        int,
        Field(**params),
    ]
