from typing import (Generic, TypeVar)

T = TypeVar("T")


class RelationshipList(list, Generic[T]):
    """
    Identical to `list[T]`, but its *type* signals
    “this collection represents an ORM relationship”.
    No behaviour is changed.
    """
    __slots__ = ()