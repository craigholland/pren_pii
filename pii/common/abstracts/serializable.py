from pii.common.utils.dataclass_transformer import DataclassTransformer
from typing import Type, TypeVar, Any, Dict

T = TypeVar("T")

class SerializableMixin:
    """Add to_dict()/from_dict() to any dataclass via DataclassTransformer."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this dataclass (and nested ones) to plain primitives."""

        return DataclassTransformer(self).as_dict

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Rehydrate a dataclass (and nested ones) from primitives."""
        dt = DataclassTransformer(cls)
        dt.import_(data)
        return dt.as_dataclass