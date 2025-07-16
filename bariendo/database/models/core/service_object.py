from sqlalchemy.orm import declared_attr, RelationshipProperty
from sqlalchemy import Column, DateTime, func, text, Text, JSON, inspect
from sqlalchemy.dialects.postgresql import UUID
from dataclasses import is_dataclass, fields, asdict
from typing import Any, Type, ClassVar, Dict, TypeVar
from bariendo.common.utils.classproperty import classproperty
from bariendo.common.utils.uuid_str import uuid_str
from bariendo.database.models.core.main import Base
from sqlalchemy.inspection import inspect
from bariendo.database.models.core.main import db
from sqlalchemy.ext.associationproxy import AssociationProxy

T = TypeVar("T")
Session = db.Session

class ServiceObject(Base):
    """
    Base mixin for *all* ORM models.  Provides id, timestamp, and metadata columns.
    Association tables and any model that does *not* map to a domain dataclass
    can simply subclass this.
    """
    __abstract__ = True
    __allow_unmapped__ = True

    def __setattr__(self, name, value):
        if name == "id":
            value = uuid_str(value)
        super().__setattr__(name, value)

    @declared_attr
    def id(cls):
        return Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))

    @declared_attr
    def date_created(cls):
        return Column(DateTime(timezone=True), server_default=func.clock_timestamp())

    @declared_attr
    def last_updated(cls):
        return Column(
            DateTime(timezone=True),
            server_default=func.clock_timestamp(),
            onupdate=func.clock_timestamp()
        )

    @declared_attr
    def data_origin(cls):
        return Column(Text, nullable=True)

    @declared_attr
    def _metadata(cls):
        return Column(JSON, nullable=True)

    @classproperty
    def dataclass(cls) -> Any:
        return getattr(cls, "__dataclass__", None)

    @classmethod
    def relationship_map(cls) -> Dict[str, Type["DeclarativeBase"]]:
        """
        Return { attr_name -> target ORM class } for:
          • 1-to-1 and 1-to-many relationships declared on *this* model
          • association_proxy attributes, mapped to the *ultimate* target class
            (skipping the intermediate association table)

        Many-to-many relationships that are *not* proxied are ignored.
        """
        mapper = inspect(cls)
        rel_map: Dict[str, Type["DeclarativeBase"]] = {}

        # ------------------------------------------------------------------
        # 1) direct relationships (1:1, 1:M)  – skip pure M:M
        # ------------------------------------------------------------------
        for rel in mapper.relationships:  # type: RelationshipProperty
            if rel.secondary is not None:  # <- indicates m2m assoc table
                continue
            rel_map[rel.key] = rel.mapper.class_

        # ------------------------------------------------------------------
        # 2) association proxies – resolve to the *remote* class
        # ------------------------------------------------------------------
        for proxy_name, proxy in vars(cls).items():
            if not isinstance(proxy, AssociationProxy):
                continue

            # The relationship on this model that the proxy rides on
            target_coll = proxy.target_collection
            rel_key = target_coll if isinstance(target_coll, str) else target_coll.key
            assoc_rel: RelationshipProperty | None = mapper.relationships.get(rel_key)
            if assoc_rel is None:
                continue  # defensive: mis-configured proxy

            # Walk one hop further using proxy.value_attr
            value_attr = getattr(proxy, "value_attr", None)
            mapped_class = assoc_rel.mapper.class_
            if value_attr:
                remote_rel = inspect(assoc_rel.mapper.class_).relationships.get(value_attr)
                if remote_rel is not None:
                    mapped_class = remote_rel.mapper.class_
                    #continue  # done – we found the real remote class

            if assoc_rel.uselist:
                mapped_class = [mapped_class]
            rel_map[proxy_name] = mapped_class

        # Remove *_assoc keys
        for key in [k for k in rel_map.keys() if k.endswith("_assocs")]:
            del rel_map[key]
        return rel_map

class ServiceObjectDC(ServiceObject):
    __abstract__ = True
    __allow_unmapped__ = True
    """
    Extends ServiceObject to tie an ORM model to a domain dataclass.
    Subclasses *must* define a __dataclass__ attribute pointing to a valid dataclass.
    Provides a generic to_dataclass() implementation.
    """

    _dc_to_orm_registry: ClassVar[Dict[Type[Any], Type["ServiceObjectDC"]]] = {}
    _orm_to_dc_registry: ClassVar[Dict[Type[Any], Type["ServiceObjectDC"]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        dc = getattr(cls, "__dataclass__", None)
        if dc is None or not is_dataclass(dc):
            raise AttributeError(f"{cls.__name__} must set __dataclass__ to its domain dataclass")

        ServiceObjectDC._dc_to_orm_registry[dc] = cls
        ServiceObjectDC._orm_to_dc_registry[cls] = dc

    def to_dataclass(self) -> Any:
        """
        Convert this ORM instance (including eagerly-loaded relationships)
        into its corresponding dataclass.
        """
        dc_cls: Type[Any] = type(self).__dataclass__
        dc_field_names = {f.name for f in fields(dc_cls)}
        payload: dict[str, Any] = {}

        # 1. Handle direct column fields
        for col in self.__table__.columns:
            if col.name in dc_field_names:
                val = getattr(self, col.name, None)
                payload[col.name] = str(val) if isinstance(val, UUID) else val

        # 2. Handle related fields (1:M, M:M, 1:1)
        unloaded = inspect(self).unloaded

        for field in dc_field_names - payload.keys():
            # Avoid evaluating unloaded attributes
            if field in unloaded:
                continue

            val = getattr(self, field, None)

            if val is None:
                payload[field] = None

            elif isinstance(val, list):
                payload[field] = [
                    item.to_dataclass() if hasattr(item, "to_dataclass") else item
                    for item in val
                ]

            elif hasattr(val, "to_dataclass"):
                payload[field] = val.to_dataclass()

            else:
                payload[field] = str(val) if isinstance(val, UUID) else val

        return dc_cls(**payload)

    @classmethod
    def from_dataclass(cls: Type[T], dc: Any) -> T:
        """Recursively converts a dataclass into its ORM model, reusing existing records if remote_id matches."""

        if dc is None:
            return None

        if isinstance(dc, list):
            return [cls.from_dataclass(item) for item in dc]

        if hasattr(dc, "__dataclass_fields__"):
            # Get correct ORM model class
            model_cls = cls._dc_to_orm_registry.get(type(dc))
            if not model_cls:
                raise ValueError(f"No ORM mapping found for dataclass {type(dc)}")

            # Shallow copy of the data
            data = dc.__dict__.copy()

            for key, value in data.items():
                # Recursively resolve nested dataclasses
                if isinstance(value, list) and value and hasattr(value[0], "__dataclass_fields__"):
                    data[key] = [cls._resolve_existing_or_new(child) for child in value]
                elif hasattr(value, "__dataclass_fields__"):
                    data[key] = cls._resolve_existing_or_new(value)

            return model_cls(**data)

        return dc  # Primitive or already an ORM object

