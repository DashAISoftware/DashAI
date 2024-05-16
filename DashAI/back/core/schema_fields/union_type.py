from typing import Type, TypeVar, Union

T = TypeVar("T")
V = TypeVar("V")


def union_type(t1: T, t2: V) -> Type[Union[T, V]]:
    return Union[t1, t2]
