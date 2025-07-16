from typing import Any, Dict, List, Type, Union, ClassVar, Optional, TypeVar
from dataclasses import is_dataclass, asdict
import importlib
import pkgutil
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from bariendo.common.abstracts.base_store import BaseStore
from bariendo.common.utils.filter import parse_filter_key, RecordFilter
from bariendo.database.models.core.service_object import ServiceObjectDC
from bariendo.database.models.core.main import db
import bariendo.database.stores as store_pkg

T = TypeVar("T")

class BaseStoreSQLAlchemy(BaseStore):
    __abstract__ = True
    _model_to_store_registry: ClassVar[Dict[Type[ServiceObjectDC], Type["BaseStoreSQLAlchemy"]]] = {}
    _Session = db.Session

    def __init_subclass__(cls, **kwargs):

        orm_model = getattr(cls, "_orm_model", None)
        if orm_model is None or not issubclass(orm_model, ServiceObjectDC):
            raise AttributeError(f"{cls.__name__} must set `_orm_model` to a subclass of ServiceObjectDC")
        cls._dc_model = cls.orm_model.dataclass
        super().__init_subclass__(**kwargs)
        BaseStoreSQLAlchemy._model_to_store_registry[orm_model] = cls

    def __init__(self, session: Session | None = None):
        if not self._model_to_store_registry:
            self._auto_discover_stores()
        self._Session = session or db.Session
        super().__init__()

    @classmethod
    def _auto_discover_stores(cls) -> None:
        for _, module_name, is_pkg in pkgutil.iter_modules(store_pkg.__path__, store_pkg.__name__ + "."):
            if not is_pkg:
                importlib.import_module(module_name)

    def get(self, pk: Union[str, int], as_orm=False) -> Optional[T]:
        with self._Session() as session:
            q = session.query(self._model)
            for rel in self._model.__mapper__.relationships:
                if rel.uselist:
                    q = q.options(joinedload(getattr(self._model, rel.key)))
            try:
                orm = q.filter(getattr(self._model, self._pk) == pk).one()
                if as_orm:
                    return orm
                return self.to_dataclass(orm)
            except NoResultFound:
                return None

    def scan(self) -> List[T]:
        with self._Session() as session:
            results = session.query(self.orm_model).order_by(self.orm_model.date_created.asc()).all()
            return [self.to_dataclass(obj) for obj in results]

    def filter(self, **kwargs) -> List[T]:
        with self._Session() as session:
            q = session.query(self.orm_model)

            for raw_key, value in kwargs.items():
                field_name, suffix = parse_filter_key(raw_key)
                if field_name in self.orm_model.relationship_map():
                    continue # Skip relationships; only filter on scalars

                col = getattr(self.orm_model, field_name)

                if suffix is None:
                    expr = (col == value)
                elif suffix == RecordFilter.Suffixes.GTE.value:
                    expr = (col >= value)
                elif suffix == RecordFilter.Suffixes.LTE.value:
                    expr = (col <= value)
                elif suffix == RecordFilter.Suffixes.NEQ.value:
                    expr = (col != value)
                elif suffix == RecordFilter.Suffixes.IN.value:
                    if not isinstance(value, (list, tuple, set)):
                        raise ValueError(f"Expected iterable for '__in' filter, got {type(value)}")
                    expr = col.in_(value)
                elif suffix == RecordFilter.Suffixes.NOTIN.value:
                    if not isinstance(value, (list, tuple, set)):
                        raise ValueError(f"Expected iterable for '__notin' filter, got {type(value)}")
                    expr = col.notin_(value)
                elif suffix == RecordFilter.Suffixes.CONTAINS.value:
                    expr = col.contains(value)
                elif suffix == RecordFilter.Suffixes.NCONTAINS.value:
                    expr = ~col.contains(value)
                else:
                    raise ValueError(f"Unsupported filter suffix __{suffix}")

                if expr is None:
                    raise ValueError(f"Unsupported filter suffix '__{suffix}'")
                q = q.filter(expr)
            return [self.to_dataclass(o) for o in q.all()]

    def _insert(self, dc: T) -> T:
        orm_model = self.orm_model.from_dataclass(dc)

        with self._Session() as session:
            session.add(orm_model)
            session.commit()
            session.refresh(orm_model)
            return self.to_dataclass(orm_model)

    def _patch(self, obj: Union[Dict, Any]) -> T:
        dc = self.to_dataclass(obj)
        patch_data = asdict(dc)
        pk_val = patch_data.get(self._pk)
        if not pk_val:
            raise ValueError(f"Missing primary key '{self._pk}' in patch data")

        with self._Session() as session:
            existing = session.get(self._model, pk_val)
            if not existing:
                raise ValueError(f"{self._model.__name__} with {self._pk}={pk_val!r} not found")

            for k, v in patch_data.items():
                if k != self._pk and hasattr(existing, k):
                    setattr(existing, k, v)

            session.commit()
            session.refresh(existing)
            return self.to_dataclass(existing)

    def _update(self, obj: Union[Dict, Any]) -> T:
        dc = self.to_dataclass(obj)
        pk_val = getattr(dc, self._pk, None)
        if not pk_val:
            return self._insert(dc)

        with self._Session() as session:
            existing = session.get(self._model, pk_val)
            if not existing:
                return self._insert(dc)

            for k, v in asdict(dc).items():
                if hasattr(existing, k):
                    setattr(existing, k, v)

            session.commit()
            session.refresh(existing)
            return self.to_dataclass(existing)

    def delete(self, pk: Union[str, int]) -> None:
        with self._Session() as session:
            instance = session.get(self._model, pk)
            if instance:
                session.delete(instance)
                session.commit()

    def get_by_remote_id(self, remote_id: Any, pk: str = "remote_id") -> Optional[T]:
        field = getattr(self._model, pk, None)
        if field is None:
            raise KeyError(f"{pk!r} not found in model {self._model.__name__}")
        stmt = select(self._model).where(field == remote_id)
        with self._Session() as session:
            result = session.execute(stmt).unique().scalar_one_or_none()
        return self.to_dataclass(result) if result else None

    def to_dataclass(self, model_instance: Any) -> T:
        if is_dataclass(model_instance):
            return model_instance
        if hasattr(model_instance, "to_dataclass"):
            return model_instance.to_dataclass()
        raise TypeError(f"Cannot convert {type(model_instance).__name__} to dataclass")



    @classmethod
    def get_store_for(cls, target: Any) -> "BaseStoreSQLAlchemy":
        if not cls._model_to_store_registry:
            cls._auto_discover_stores()

        if is_dataclass(target):
            dc_cls = target if isinstance(target, type) else type(target)
            orm_cls = ServiceObjectDC._dc_to_orm_registry.get(dc_cls)
        elif isinstance(target, ServiceObjectDC):
            orm_cls = type(target)
        elif isinstance(target, type) and issubclass(target, ServiceObjectDC):
            orm_cls = target
        else:
            raise TypeError(f"Cannot resolve ORM model from {target!r}")

        if orm_cls is None:
            raise LookupError(f"No ORM↔dataclass mapping for {target!r}")
        store_cls = cls._model_to_store_registry.get(orm_cls)
        if store_cls is None:
            raise LookupError(f"No store registered for ORM model {orm_cls!r}")

        inst = store_cls()
        inst._Session = db.Session
        return inst
