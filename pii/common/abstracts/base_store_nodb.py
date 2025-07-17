from typing import Union, List, Optional, Any, Dict, TypeVar
from pii.common.utils.filter import parse_filter_key, RecordFilter
from uuid import uuid4
from dataclasses import is_dataclass, asdict, fields
from pii.common.utils.dataclass_transformer import DataclassTransformer
from pii.common.abstracts.base_store import BaseStore

T = TypeVar("T")
class BaseStore_NoDB(BaseStore):
    """
    In-memory store implementation.
    """
    __abstract__ = True
    _store = {}  # Shared class-level backing store

    def __init__(self, dc_model: Optional[T] = None):
        self._dc_model = dc_model or self._dc_model
        super().__init__()

        cls_name = self.__class__.__name__
        self._cls_name = cls_name

        # Reset partition for test isolation
        self._store[cls_name] = {}

    @classmethod
    def _init_store_for_tests(cls) -> None:
        """ Clear all partitions (used in tests) """
        for key in cls._store.keys():
            cls._store[key] = {}

    def _validate_object(self, obj: Any) -> Any:
        """ Ensure object is correct type or convert via from_dict() """
        if isinstance(obj, dict):
            obj = self.from_dict(obj)
        if not isinstance(obj, self.dc_model):
            raise TypeError(self.Error.TYPEERROR_MODELTYPE.format(self.dc_model))
        return obj

    def get(self, pk: str, default: Any = None) -> Any:
        return self._store[self._cls_name].get(pk, default)

    def _insert(self, obj: Any) -> Any:
        obj = self._validate_object(obj)
        pk = getattr(obj, self.dc_model._pk, None)
        if not pk:
            pk = str(uuid4())
            setattr(obj, self.dc_model._pk, pk)
        self._store[self._cls_name][pk] = obj
        return obj

    def _patch(self, obj):
        """
        Update only the provided fields of an existing object.
        Preserves any fields not included in the patch data.
        """
        if is_dataclass(obj):
            obj_id = getattr(obj, "id", None)
        else:
            obj_id = obj.get("id")

        if obj_id is None:
            raise ValueError("Cannot patch without an ID")

        # Get the existing object
        existing = self.get(obj_id)
        if existing is None:
            raise ValueError(f"Object with primary key {obj_id} not found")

        # Create a dictionary from the existing object
        existing_dict = asdict(existing) if is_dataclass(existing) else existing.copy()

        # Create a dictionary from the patch object, excluding None values
        patch_dict = {}
        if is_dataclass(obj):
            # For dataclass objects, extract non-None fields
            for field in fields(obj):
                value = getattr(obj, field.name)
                if value is not None:
                    patch_dict[field.name] = value
        else:
            # For dictionaries, extract non-None fields
            patch_dict = {k: v for k, v in obj.items() if v is not None}

        # Update the existing dictionary with the patch data
        existing_dict.update(patch_dict)

        # Convert back to a dataclass if needed
        if is_dataclass(existing):
            patched = type(existing)(**existing_dict)
        else:
            patched = existing_dict

        # Update the store
        self._store[obj_id] = patched
        return patched

    def _update(self, obj: Any) -> Any:
        obj = self._validate_object(obj)
        pk = getattr(obj, self._pk, None)
        if not pk:
            raise ValueError(self.Error.VALUEERROR_PRIMARYKEY.format(self._pk))

        self._store[self._cls_name][pk] = obj
        return obj

    def patch(self, obj: Any) -> Any:
        return self._patch(obj)

    def scan(self) -> List[Any]:
        return list(self._store[self._cls_name].values())

    def filter(self, **kwargs) -> List[Any]:
        if records := self.scan():
            return RecordFilter(records).filter(**kwargs).results
        return []

    def delete(self, pk: str) -> bool:
        if pk in self._store[self._cls_name]:
            del self._store[self._cls_name][pk]
            return True
        else:
            raise ValueError(self.Error.VALUEERROR_PRIMARYKEY_NOTFOUND.format(pk))

    def get_by_remote_id(self, remote_id: Any, pk: str = "remote_id") -> Optional[T]:
        for obj in self._store.values():
            if hasattr(obj, pk) and getattr(obj, pk) == remote_id:
                return obj
        return None