import json
import dataclasses
from dataclasses import is_dataclass, fields
from typing import Any, Type, TypeVar, get_origin, get_args, Union, Optional, Dict
from uuid import UUID
from datetime import datetime

from pii.common.abstracts.base_dataclass import RelationshipList  # ← new import

T = TypeVar("T")


class DataclassTransformer:
    """
    Transforms between dataclass instances, dicts, and JSON strings.

    Usage:
        transformer = DataclassTransformer(MyDataclass)
        transformer.import_(data_dict)      # dict → dataclass
        transformer.import_(json_str)       # JSON → dataclass
        instance = transformer.as_dataclass # get dataclass
        as_dict  = transformer.as_dict      # dataclass → dict
        as_json  = transformer.as_json      # dataclass → JSON
    """

    _COERCIONS = {
        (UUID, str): UUID,
        (datetime, str): datetime.fromisoformat,
        (float, (int, str)): float,
        (int, str): int,
    }

    def __init__(self, dc_or_instance: Union[Type[T], T]):
        if is_dataclass(dc_or_instance):
            if isinstance(dc_or_instance, type):
                self._dataclass: Type[T] = dc_or_instance
                self._data: Optional[T] = None
            else:
                self._dataclass = type(dc_or_instance)
                self._data = dc_or_instance
        else:
            raise TypeError("Expected a dataclass class or instance.")

    @staticmethod
    def get_dataclass(obj: Any) -> Union[T, None]:
        """
            Returns the dataclass type from a dataclass object or instance.

            Args:
                obj: An object that might be a dataclass type or instance

            Returns:
                The dataclass type if input is a dataclass type or instance, None otherwise
            """
        if is_dataclass(obj):
            if isinstance(obj, type):
                # It's a dataclass type (class itself)
                return obj
            else:
                # It's a dataclass instance
                return type(obj)

        # Not a dataclass
        return None

    def import_(self, src: Union[Dict[str, Any], str, T]) -> "DataclassTransformer":
        # JSON → dict
        if isinstance(src, str):
            try:
                src = json.loads(src)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        # dataclass instance → dict
        if is_dataclass(src) and not isinstance(src, dict):
            src = dataclasses.asdict(src)

        if not isinstance(src, dict):
            raise TypeError(f"Cannot import from type {type(src).__name__}")

        # build or patch
        if self._data is None:
            self._data = self._build(self._dataclass, src)
        else:
            self._patch(self._data, src)

        return self

    @property
    def as_dataclass(self) -> T:
        return self._data  # type: ignore

    @property
    def as_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self._data) if self._data is not None else {}

    @property
    def as_json(self) -> str:
        def default(o: Any) -> str:
            if isinstance(o, (UUID, datetime)):
                return str(o)
            raise TypeError(f"{type(o).__name__} is not JSON serializable")
        return json.dumps(self.as_dict, default=default)

    def _build(self, cls: Type[T], data: Dict[str, Any]) -> T:
        kwargs: Dict[str, Any] = {}
        for f in fields(cls):
            if f.name in data:
                val = data[f.name]
                kwargs[f.name] = self._coerce_field(f.type, val)
        return cls(**kwargs)  # type: ignore

    def _patch(self, instance: T, patch: Dict[str, Any]) -> None:
        """
        Patch an existing dataclass instance with new values.

        - For primitive or simple container fields, we coerce & setattr.
        - For nested dataclass fields, we delegate to a sub-transformer.
        - For RelationshipList[T], we iterate incoming list; if element T
          already exists at same index, patch it, else build a new T.
        """
        from pii.common.abstracts.base_dataclass import RelationshipList

        for f in fields(instance):
            if f.name not in patch:
                continue

            new_val = patch[f.name]
            field_type = f.type
            origin = get_origin(field_type)

            # 1) Nested dataclass: Dict → patch existing dataclass
            if is_dataclass(field_type) and isinstance(new_val, dict):
                current = getattr(instance, f.name)
                # Patch in place
                patched = DataclassTransformer(current).import_(new_val).as_dataclass
                setattr(instance, f.name, patched)
                continue

            # 2) RelationshipList[T]: list of nested dataclasses
            if origin is RelationshipList and isinstance(new_val, list):
                elem_type = get_args(field_type)[0]
                current_list = getattr(instance, f.name) or RelationshipList()
                updated_list = RelationshipList()
                for idx, elem_data in enumerate(new_val):
                    # If existing dataclass at same index, patch it
                    if idx < len(current_list) and is_dataclass(elem_type):
                        transformer = DataclassTransformer(current_list[idx])
                        transformer.import_(elem_data)
                        updated_list.append(transformer.as_dataclass)
                    else:
                        # Build a fresh one
                        built = DataclassTransformer(elem_type).import_(elem_data).as_dataclass
                        updated_list.append(built)
                setattr(instance, f.name, updated_list)
                continue

            # 3) Fallback for everything else
            coerced = self._coerce_field(field_type, new_val)
            setattr(instance, f.name, coerced)

    def _coerce_field(self, ftype: Type, value: Any) -> Any:
        origin = get_origin(ftype)
        args = get_args(ftype)

        # Handle RelationshipList[T] first
        if origin is RelationshipList:
            elem_type = args[0]
            # Build nested dataclasses or simple coercion for each element
            return [
                self._coerce_field(elem_type, v)
                for v in value
            ]

        # Optional[T]
        if origin is Union and type(None) in args:
            non_none = next(a for a in args if a is not type(None))
            return None if value is None else self._coerce_field(non_none, value)

        # List[T]
        if origin is list and args:
            return [
                self._coerce_field(args[0], v)
                for v in value
            ]

        # Dict[K, V]
        if origin is dict and len(args) == 2:
            return {
                self._coerce_field(args[0], k): self._coerce_field(args[1], v)
                for k, v in value.items()
            }

        # Nested dataclass
        if is_dataclass(ftype):
            if isinstance(value, ftype):
                return value
            if isinstance(value, dict):
                return DataclassTransformer(ftype).import_(value).as_dataclass

        # Simple coercions
        for (target, src_types), fn in self._COERCIONS.items():
            if ftype is target and isinstance(value, src_types):
                return fn(value)

        # Fallback
        return value
