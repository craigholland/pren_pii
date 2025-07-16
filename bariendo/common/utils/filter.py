
from typing import Union, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import is_dataclass, fields


def parse_filter_key(key: str) -> Tuple[str, Optional[str]]:
    """
    Parse a filter key into its attribute name and suffix (if any).
    For example, "expiration_date__gte" returns ("expiration_date", "gte").

    Parameters:
        key (str): The filter key.

    Returns:
        Tuple[str, Optional[str]]: A tuple of (attribute, suffix).

    Raises:
        ValueError: If key format is invalid (more than one '__').
    """
    parts = key.split("__")
    if len(parts) == 1:
        return parts[0], None
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        raise ValueError(f"Invalid filter key format: {key}")


class RecordFilter:
    """
    A reusable filter class for a collection of records.

    Accepts a list of records (which can be dictionaries, dataclass instances, or plain objects)
    and provides chainable methods to filter and sort them based on attribute values.
    After applying filters and/or sorting, the final results are available via the `results` property.

    Example:
        results = (RecordFilter(my_list_of_records)
                   .filter(param1__in=["Home", "Away"], param2__lte=100, param3="John")
                   .sort("param2__desc")
                   .results)
    """

    class Suffixes(Enum):
        """Supported suffixes for filter operations."""
        GTE = 'gte'
        LTE = 'lte'
        IN = 'in'
        NOTIN = 'notin'
        NEQ = 'neq'
        CONTAINS = 'contains'
        NCONTAINS = 'ncontains'

        @classmethod
        def values(cls) -> List[str]:
            return [member.value for member in cls]

    class RecordType(Enum):
        """Supported record types."""
        DICT = "DICT"
        DATACLASS = "DATACLASS"
        OBJECT = "OBJECT"

    def __init__(self, records: List[Any], strict_attr: bool = True, ignore_private_attrs: bool = True):
        """
        Initialize a RecordFilter instance.

        :param records: A list of records (dicts, dataclass instances, or objects).
        :param strict_attr: If True, require that all records have exactly the same attributes.
        :param ignore_private_attrs: If True, exclude attributes that start with an underscore.
        """
        self.records: List[Any] = records
        self._strict_attr: bool = strict_attr
        self._ignore_private_attrs: bool = ignore_private_attrs
        self._attrs: List[str] = []
        self._obj_type: Optional[RecordFilter.RecordType] = None
        self._obj_type_name: str = ""
        self._results: List[Any] = []
        self._validate_records()

    def _get_obj_type(self, obj: Any) -> RecordType:
        """
        Determine the record type for an object.

        :param obj: A record object.
        :return: RecordType.DICT, RecordType.DATACLASS, or RecordType.OBJECT.
        """
        if is_dataclass(obj):
            return RecordFilter.RecordType.DATACLASS
        elif isinstance(obj, dict):
            return RecordFilter.RecordType.DICT
        else:
            return RecordFilter.RecordType.OBJECT

    def _get_obj_attrs(self, obj: Any) -> List[str]:
        """
        Extract attribute names from a record.

        For dicts, returns keys; for dataclasses, field names; for objects, names from vars().

        :param obj: A record.
        :return: List of attribute names.
        """
        if isinstance(obj, dict):
            attrs = list(obj.keys())
        elif is_dataclass(obj):
            attrs = [f.name for f in fields(obj)]
        else:
            attrs = list(vars(obj).keys())
        if self._ignore_private_attrs:
            attrs = [a for a in attrs if not a.startswith('_')]
        return attrs

    def _get_obj_name(self, obj: Any) -> str:
        """
        Get the name of the object.

        Returns __name__ if obj is a class; otherwise, returns the class name.

        :param obj: A record.
        :return: The object's name.
        """
        if isinstance(obj, type):
            return obj.__name__
        return type(obj).__name__

    def _is_valid_object(self, obj: Any) -> bool:
        """
        Validate that a record is consistent with the initial record's type, name, and attributes.

        Sets the expected values on the first record encountered.

        :param obj: A record.
        :return: True if valid, False otherwise.
        """
        current_type = self._get_obj_type(obj)
        current_name = self._get_obj_name(obj)
        current_attrs = self._get_obj_attrs(obj)
        if self._obj_type is not None:
            attr_check = True
            if self._strict_attr and self._obj_type == RecordFilter.RecordType.DICT:
                attr_check = sorted(self._attrs) == sorted(current_attrs)
            return (self._obj_type == current_type and
                    self._obj_type_name == current_name and
                    attr_check)
        else:
            self._obj_type = current_type
            self._obj_type_name = current_name
            self._attrs = current_attrs
            return True

    def _validate_records(self) -> None:
        """
        Ensure all provided records are of consistent type, name, and attributes.

        :raises TypeError: If inconsistency is found.
        """
        for record in self.records:
            if not self._is_valid_object(record):
                raise TypeError(
                    f"Inconsistent record found:\n"
                    f"Expected: type {self._obj_type}, name {self._obj_type_name}, attrs {self._attrs}\n"
                    f"Found: type {self._get_obj_type(record)}, name {self._get_obj_name(record)}, "
                    f"attrs {self._get_obj_attrs(record)}"
                )

    def _validate_kwargs(self, kwargs: dict) -> None:
        """
        Validate keyword arguments used for filtering.

        :param kwargs: Filter criteria.
        :raises ValueError: If an attribute or suffix is invalid.
        """
        for kw in kwargs.keys():
            attr, sfx = self._parse_filter_key(kw)
            if attr not in self._attrs:
                raise ValueError(f"Attribute '{attr}' not found in {self._attrs}")
            if sfx and sfx.lower() not in RecordFilter.Suffixes.values():
                valid = [f"__{s}" for s in RecordFilter.Suffixes.values()]
                raise ValueError(f"Suffix '__{sfx}' not supported. Valid suffixes: {valid}")

    @staticmethod
    def _parse_filter_key(key: str) -> Tuple[str, Optional[str]]:
        """
        Parse a filter key into its base attribute and optional suffix.

        e.g. "expiration_date__gte" -> ("expiration_date", "gte")

        :param key: The filter key.
        :return: A tuple (attribute, suffix) where suffix may be None.
        :raises ValueError: If key format is invalid.
        """
        parts = key.split("__")
        if len(parts) == 1:
            return parts[0], None
        elif len(parts) == 2:
            return parts[0], parts[1].lower()
        else:
            raise ValueError(f"Invalid filter key format: {key}")

    def _get_attr(self, obj: Any, attr: str, default: Any = None) -> Any:
        """
        Get an attribute's value from a record.

        Works for dicts and objects.

        :param obj: A record.
        :param attr: The attribute name.
        :param default: Default value if missing.
        :return: The attribute value.
        """
        if self._obj_type == RecordFilter.RecordType.DICT:
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    def _match_record(self, record: Any, params: dict) -> bool:
        """
        Check if a record matches all the filter conditions.

        :param record: The record to test.
        :param params: Dictionary of filter parameters.
        :return: True if the record matches all parameters, False otherwise.
        """
        for key, value in params.items():
            attr, sfx = self._parse_filter_key(key)
            attr_val = self._get_attr(record, attr)
            if sfx is None:
                if attr_val != value:
                    return False
            else:
                # Validate type consistency for non-list conditions
                if sfx not in (RecordFilter.Suffixes.IN.value,
                               RecordFilter.Suffixes.NOTIN.value,
                               RecordFilter.Suffixes.NEQ.value):
                    if not isinstance(value, type(attr_val)):
                        return False
                if sfx == RecordFilter.Suffixes.IN.value:
                    if attr_val not in value:
                        return False
                elif sfx == RecordFilter.Suffixes.NOTIN.value:
                    if attr_val in value:
                        return False
                elif sfx == RecordFilter.Suffixes.GTE.value:
                    if attr_val < value:
                        return False
                elif sfx == RecordFilter.Suffixes.LTE.value:
                    if attr_val > value:
                        return False
                elif sfx == RecordFilter.Suffixes.NEQ.value:
                    if attr_val == value:
                        return False
                elif sfx == RecordFilter.Suffixes.CONTAINS.value:
                    if value not in attr_val:
                        return False
                elif sfx == RecordFilter.Suffixes.NCONTAINS.value:
                    if value in attr_val:
                        return False
                else:
                    return False
        return True

    def filter(self, **kwargs) -> 'RecordFilter':
        """
        Filter records based on given keyword arguments.

        Supports suffixes such as __gte, __lte, __in, __notin, __neq, __contains, __ncontains.
        The filtered results are stored in the `results` property.

        :param kwargs: Filter criteria.
        :return: self, to allow chaining.
        """
        if self.records:
            self._validate_kwargs(kwargs)
            filtered = []
            for record in self.records:
                if self._match_record(record, kwargs):
                    filtered.append(record)
            self._results = filtered
        else:
            self._results = []
        return self


    def sort(self, sort_keys: Union[str, List[str]]) -> 'RecordFilter':
        """
        Sort records based on one or more keys.

        Each sort key may specify ordering using '__asc' or '__desc'.
        For example: "expiration_date__desc" sorts by expiration_date descending.

        :param sort_keys: A single sort key or list of sort keys.
        :return: self, to allow chaining.
        :raises AttributeError: If the sort order is not recognized.
        """
        if isinstance(sort_keys, str):
            sort_keys = [sk.strip() for sk in sort_keys.split(',')]
        # Use current filtered results if available; else the original records.
        records = self.results if self.results else self.records
        # Process sort keys in reverse order (to respect multi-key sorting)
        for key in reversed(sort_keys):
            attr, order = self._parse_filter_key(key)
            order = order or 'asc'
            order = order.lower()
            if order not in ['asc', 'desc']:
                raise AttributeError("Sort order must be '__asc' or '__desc'")
            records = sorted(records, key=lambda r: self._get_attr(r, attr),
                             reverse=(order == 'desc'))
        self._results = records
        return self

    @property
    def results(self) -> List[Any]:
        """
        Return the filtered and/or sorted results.

        :return: A list of matching records.
        """
        return self._results

    def top(self, n: int) -> List[Any]:
        """
        Return the top n records from the results.

        :param n: Number of records.
        :return: A list of the top n records.
        """
        return self._results[:n] if len(self._results) >= n else self._results

    def bottom(self, n: int) -> List[Any]:
        """
        Return the bottom n records from the results.

        :param n: Number of records.
        :return: A list of the bottom n records.
        """
        return self._results[-n:] if len(self._results) >= n else self._results

