from abc import ABC
from typing import Dict, Any, TypeVar, Generic, Optional, Type
from dataclasses import is_dataclass
from bariendo.common.abstracts.base_store import BaseStore
T = TypeVar('T')


class BaseProfile(Generic[T], ABC):
    """
    Base class for all Profiles which provide a consistent interface to domain objects
    regardless of the underlying storage mechanism.
    """
    # Class-level default attributes to be overridden by subclasses
    field_mapping: Dict[str, str] = {}
    external_pk_field: str = ""

    # Class attribute for the store
    _store: BaseStore = None

    def __init__(
            self,
            instance: Optional[T] = None,
            field_mapping: Optional[Dict[str, str]] = None,
            external_pk_field: Optional[str] = None
    ):
        """
        Initialize a Profile with an optional instance and mapping overrides.

        Args:
            instance: Optional dataclass instance to wrap
            field_mapping: Optional override for the class-level field_mapping
            external_pk_field: Optional override for the class-level external_pk_field
        """
        # Use instance-level overrides if provided, otherwise use class defaults
        self._field_mapping = field_mapping if field_mapping is not None else self.__class__.field_mapping
        self._external_pk_field = external_pk_field if external_pk_field is not None else self.__class__.external_pk_field

        # Initialize the instance
        self._instance = instance

    def __getattr__(self, name: str) -> Any:
        """
        Pass-through attribute access to the underlying instance.

        Args:
            name: Name of the attribute to access

        Returns:
            The value of the attribute from the underlying instance

        Raises:
            AttributeError: If the attribute doesn't exist on the instance
        """
        if self._instance is None:
            raise AttributeError(f"No instance available for attribute '{name}'")
        return getattr(self._instance, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Handle attribute assignment, routing to instance when appropriate.

        Args:
            name: Name of the attribute to set
            value: Value to assign to the attribute
        """
        # Internal attributes are set directly on the profile
        if name.startswith('_'):
            super().__setattr__(name, value)
            return

        # Other attributes are passed through to the instance
        if self._instance is not None:
            setattr(self._instance, name, value)
        else:
            # If no instance exists yet, set directly (might be used for initialization)
            super().__setattr__(name, value)

    @classmethod
    def from_external_data(cls, data: Dict[str, Any], **kwargs) -> 'BaseProfile[T]':
        """
        Create a Profile instance from external data using the field mapping.

        Args:
            data: External data dictionary
            **kwargs: Additional arguments to pass to the constructor

        Returns:
            A new Profile instance with the imported data
        """
        # Create a new instance of the appropriate dataclass type
        instance_type = cls._get_dataclass_type()

        # Map external field names to internal attribute names
        mapped_data = {}
        field_mapping = kwargs.get('field_mapping', cls.field_mapping)

        for external_field, internal_field in field_mapping.items():
            if external_field in data:
                mapped_data[internal_field] = data[external_field]

        # Create the dataclass instance
        instance = instance_type(**mapped_data)

        # Create and return the profile
        return cls(instance=instance, **kwargs)

    @classmethod
    def _get_dataclass_type(cls) -> Type[T]:
        """
        Get the dataclass type that this profile manages.
        This method should be implemented by subclasses.

        Returns:
            The dataclass type
        """
        raise NotImplementedError("Subclasses must implement _get_dataclass_type")

    def save(self) -> T:
        """
        Save the current instance to the store.

        Returns:
            The updated instance after saving
        """
        if self._instance is None:
            raise ValueError("Cannot save: no instance available")

        # Use the class's store to save the instance
        result = self.__class__._store.put(self._instance)
        self._instance = result
        return result

    def load(self, pk: Any) -> T:
        """
        Load an instance by primary key.

        Args:
            pk: Primary key value

        Returns:
            The loaded instance
        """
        # Use the class's store to load the instance
        result = self.__class__._store.get(pk)
        self._instance = result
        return result

    def load_by_external_id(self, external_id: Any) -> T:
        """
        Load an instance by external ID.

        Args:
            external_id: External ID value

        Returns:
            The loaded instance
        """
        # Use the class's store to find by the external ID field
        result = self.__class__._store.get_by_remote_id(external_id)
        self._instance = result
        return result