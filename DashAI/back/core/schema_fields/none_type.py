from typing import Optional, Type, TypeVar

T = TypeVar("T")


def none_type(t: T) -> Type[Optional[T]]:
    return Optional[t]
