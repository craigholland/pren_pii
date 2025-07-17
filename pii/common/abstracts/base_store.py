from typing import List, Optional, Any, TypeVar
from abc import ABC, abstractmethod
from dataclasses import is_dataclass, fields
from pii.common.utils.dataclass_transformer import DataclassTransformer
from pii.common.utils.classproperty import classproperty

T = TypeVar("T")

class BaseStore(ABC):
    """
    Abstract base class for all store implementations (in-memory or persistent).
    Defines the interface for CRUD operations and object conversion.
    """
    _orm_model = None
    _dc_model = None
    _dc_transformer = DataclassTransformer
    _profile_registry = {}

    class Error:
        ATTRERROR_MODEL = "Model `{0}` does not have attribute `{1}`"
        TYPEERROR_MODELTYPE = "Object must be of type '{0}' or dict"
        TYPEERROR_OBJECTTYPE = "Object type must be of type `{0}`"
        VALUEERROR_PRIMARYKEY = "Object must contain primary key '{0}'"
        VALUEERROR_PRIMARYKEY_NOTFOUND = "Object with primary key '{0}` not found"
        UNIMPLEMENTED_ERROR = "`{0}` - `{1}` is not implemented for this class. Please implement in the derived class."
        MISSING_MODEL = "`{0}` - `{1}` must contain a `_dc_model` attribute. Found `{2}`"
        VALUEERROR_MULTI_MATCH = "Multiple records match criteria {0}"

    def __init__(self, dc_model=None):
        if dc_model:
            if dc := DataclassTransformer.get_dataclass(dc_model):
                self._dc_model = dc
            else:
                raise ValueError(f"Store `dc_model` must be a dataclass; got {dc_model}")

    def __init_subclass__(cls, **kwargs):
        if not cls._is_abstract:
            if not hasattr(cls, "_dc_model") or cls._dc_model is None:
                raise AttributeError(BaseStore.Error.MISSING_MODEL.format(
                    cls.__module__, cls.__name__, getattr(cls, '_dc_model', None)
                ))
            cls.dc_model._register_store(cls)


    @classproperty
    def _is_abstract(cls):
        return cls.__dict__.get('__abstract__', False)

    @classproperty
    def orm_model(self) -> Any:
        """Return the ORM-model class associated with this store."""
        return self._orm_model

    @classproperty
    def dc_model(self) -> Any:
        """Return the dataclass-model class associated with this store."""
        return self._dc_model

    @abstractmethod
    def get(self, pk: str) -> Any:
        """Retrieve an object by its primary key."""
        pass

    def get_or_create(self, **kwargs) -> Any:  # noqa: ANN401
        """Return the *unique* record matching ``kwargs`` or create it.

        Parameters
        ----------
        **kwargs
            Field lookups passed directly to :meth:`filter`.

        Returns
        -------
        Any
            The existing or newly‑created domain object (type depends on store).

        Raises
        ------
        ValueError
            * If more than one record matches the given criteria.
        """
        dc = self.from_dict(kwargs)
        matches = self.filter(**kwargs)

        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(BaseStore.Error.VALUEERROR_MULTI_MATCH.format(kwargs))

        # None found – create via dataclass constructor then persist
        if not self.dc_model:
            raise AttributeError("Cannot create record – `_dc_model` not set on store")

        # Strip pk if provided
        setattr(dc, dc._pk, None)
          # type: ignore[arg-type, call-arg]
        return self.put(dc)


    def put(self, obj: Any) -> Any:
        """
        Insert or update an object in the store.

        This is the main public method for persisting objects:
        1. If no primary key is present, the object is inserted as new
        2. If a primary key is present, a full update is attempted
        3. If the update fails (e.g., record not found), a patch operation is attempted

        :param obj: The object to persist (dataclass instance or dict)
        :return: The persisted object
        """
        # Determine if the primary key exists in the object
        pk = getattr(obj, "id", None) if is_dataclass(obj) else obj.get("id") if isinstance(obj, dict) else None

        # If no primary key, insert as new object
        if pk is None:
            return self._insert(obj)

        try:
            # Attempt a full update if primary key exists
            return self._update(obj)
        except ValueError as e:
            # If update fails (typically because object doesn't exist),
            # fallback to patch operation
            if str(e).startswith(f"Object with primary key") and "not found" in str(e):
                return self._patch(obj)
            # Re-raise any other ValueError
            raise

    @abstractmethod
    def _insert(self, obj: Any) -> Any:
        """Insert a new object into the store."""
        pass

    @abstractmethod
    def _patch(self, obj: Any) -> Any:
        """Patch/update an existing object using partial data."""
        pass

    @abstractmethod
    def _update(self, obj: Any) -> Any:
        """Replace or fully update an existing object."""
        pass

    @abstractmethod
    def scan(self) -> List[Any]:
        """Retrieve all objects from the store."""
        pass

    @abstractmethod
    def filter(self, **kwargs) -> List[Any]:
        """Filter objects by given keyword arguments."""
        pass

    @abstractmethod
    def delete(self, pk: str) -> None:
        """Delete an object from the store by its primary key."""
        pass

    def from_dict(self, data: dict) -> Any:
        """
        Create a model instance from a dictionary using the transformer.
        For DB-backed stores, this typically returns an ORM model.
        For NoDB stores, this returns the dataclass itself.
        """

        transformer = self._dc_transformer(self.dc_model)
        transformer.import_(data)
        return transformer.as_dataclass

    def to_dict(self, obj: Any, no_private: bool = True) -> dict:
        """
        Convert an object to its dictionary representation.
        If the object is not a dataclass, tries to convert it first via `.to_dataclass()`.
        """
        if not is_dataclass(obj):
            if hasattr(obj, "to_dataclass"):
                obj = obj.to_dataclass()
            else:
                raise TypeError(f"Cannot convert object of type {type(obj)} to dict")

        transformer = self._dc_transformer(obj)
        data = transformer.as_dict
        if no_private:
            return {k: v for k, v in data.items() if not k.startswith("_")}
        return data
