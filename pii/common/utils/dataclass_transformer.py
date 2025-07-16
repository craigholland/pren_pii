import json
import dataclasses
from dataclasses import is_dataclass, fields
from typing import Any, Type, get_origin, get_args, Union, TypeVar
from uuid import UUID
from datetime import datetime

T = TypeVar("T")
class DataclassTransformer:

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
    def __init__(self, dc_or_instance: Any):
        if is_dataclass(dc_or_instance):
            if isinstance(dc_or_instance, type):
                self._dataclass = dc_or_instance
                self._data = None
            else:
                self._dataclass = type(dc_or_instance)
                self._data = dc_or_instance
        else:
            raise TypeError("Expected a dataclass or a dataclass instance.")

    def import_(self, obj: Any):
        if isinstance(obj, dict):
            self._import_dict(obj)
        elif is_dataclass(obj):
            self._import_dataclass(obj)
        elif isinstance(obj, str):
            self._import_json(obj)
        else:
            raise TypeError(f"Unsupported input type: {type(obj)}")

    def _import_dict(self, input_dict: dict):
        if self._data is None:
            self._data = self._build(self._dataclass, input_dict)
        else:
            self._patch(self._data, input_dict)

    def _import_json(self, input_json: str):
        parsed = json.loads(input_json)
        if not isinstance(parsed, dict):
            raise ValueError("Parsed JSON must be a dictionary.")
        self._import_dict(parsed)

    def _import_dataclass(self, instance: Any):
        if self._data is None:
            self._data = instance
        else:
            self._patch(self._data, dataclasses.asdict(instance))

    @property
    def as_dataclass(self) -> Any:
        return self._data

    @property
    def as_dict(self) -> dict:
        return dataclasses.asdict(self._data) if self._data else {}

    @property
    def as_json(self) -> str:
        def default(obj):
            if isinstance(obj, (UUID, datetime)):
                return str(obj)
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        return json.dumps(self.as_dict, default=default)

    def _build(self, dc_cls: Type, data: dict):
        kwargs = {}
        for f in fields(dc_cls):
            if f.name not in data:
                continue
            val = data[f.name]
            rel_fields_dct = dc_cls.relationship_fields()
            if f.name in rel_fields_dct and isinstance(val, (list, tuple)):
                rel_list = []
                for v in val:
                    child_store = rel_fields_dct[f.name]._store()
                    child = child_store.get_or_create(**v)
                    rel_list.append(child)
                kwargs[f.name] = rel_list
            else:
                kwargs[f.name] = self._coerce_field(f.type, val)
        return dc_cls(**kwargs)

    def _patch(self, instance: Any, patch_data: dict):
        for f in fields(instance):
            if f.name not in patch_data:
                continue
            new_val = patch_data[f.name]
            current_val = getattr(instance, f.name)

            # Recursive patch if current value is a dataclass and new_val is a dict
            if is_dataclass(current_val) and isinstance(new_val, dict):
                self._patch(current_val, new_val)
            else:
                coerced = self._coerce_field(f.type, new_val)
                setattr(instance, f.name, coerced)

    def _coerce_field(self, ftype: Type, value: Any) -> Any:
        origin = get_origin(ftype)
        args = get_args(ftype)
        if is_dataclass(ftype):
            if isinstance(value, ftype):
                return value
            elif isinstance(value, dict):
                return self._build(ftype, value)

        # Handle Optional[T]
        if origin is Union and type(None) in args:
            non_none = [a for a in args if a is not type(None)][0]
            return None if value is None else self._coerce_field(non_none, value)

        # Handle List[T]
        if origin is list and args:
            inner = args[0]
            return [self._coerce_field(inner, v) for v in value]

        # Handle Dict[K, V]
        if origin is dict and len(args) == 2:
            k_type, v_type = args
            return {
                self._coerce_field(k_type, k): self._coerce_field(v_type, v)
                for k, v in value.items()
            }

        # Handle nested dataclass
        if is_dataclass(ftype) and isinstance(value, dict):
            return self._build(ftype, value)

        # Simple coercion rules
        if ftype == UUID and isinstance(value, str):
            return UUID(value)
        if ftype == datetime and isinstance(value, str):
            return datetime.fromisoformat(value)
        if ftype == float and isinstance(value, (int, str)):
            return float(value)
        if ftype == int and isinstance(value, str):
            return int(value)

        return value
