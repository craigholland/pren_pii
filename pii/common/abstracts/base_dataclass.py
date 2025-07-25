from dataclasses import fields, Field
from types import UnionType
from typing import (
    Any, TypeVar, ClassVar, get_args, get_origin, Union,
    get_type_hints, ForwardRef, Optional
)
from datetime import date

from pii.common.utils.uuid_str import uuid_str, UUIDStr
from pii.common.abstracts.serializable import SerializableMixin
from pii.common.abstracts.relationship_list import RelationshipList
from pii.common.utils.dateparser import DateParser


"""Common base mix‑in for domain dataclasses.

Features
--------
* **UUID primary‑key normalisation** – any attribute named ``id`` (or the
  value of :pyattr:`_pk`) is coerced to a canonical UUID string via
  :pyfunc:`prenuvo_pii.common.utils.uuid_str.uuid_str` every time it is
  assigned.
* **Automatic runtime type‑checking** on construction (``__post_init__``)
  and via :py:meth:`validate_types`. Static flag
  :pyattr:`__skip_type_validation__` allows per‑class opt‑out.
* **Relationship introspection** – :py:meth:`relationship_fields` mirrors the
  ORM‑side helper and returns a mapping of ``field_name → target dataclass``
  for all :pyclass:`~prenuvo_pii.common.typing.relationship.RelationshipList`
  fields.

Python 3.12 compliant – subclasses the plain ``list`` class rather than the
``list[T]`` generic alias.
"""

__all__ = ["BaseDataclass"]

T = TypeVar("T")

class BaseDataclass(SerializableMixin):
    """Mixin meant to be inherited *before* applying :pyfunc:`dataclasses.dataclass`.

    Example
    -------
    ```python
    @dataclass
    class Ingredient(BaseDataclass):
        id: str | None = None
        name: str | None = None
    ```
    """

    # ------------------------------------------------------------------
    #  Configuration hooks
    # ------------------------------------------------------------------
    _pk: ClassVar[str] = "id"  # name of the primary‑key attribute
    __skip_type_validation__: ClassVar[bool] = False  # opt‑out flag for heavy imports
    _store: ClassVar = None

    # ------------------------------------------------------------------
    #  Primary‑key normalisation
    # ------------------------------------------------------------------
    def __setattr__(self, name: str, value: Any):
        if name == self._pk:
            value = uuid_str(value)
        super().__setattr__(name, value)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return getattr(self, self.get_pk(), None) == getattr(other, self.get_pk(), None)

    def __hash__(self):
        return hash(getattr(self, self.get_pk(), None))
    # ------------------------------------------------------------------
    #  Automatic post‑init validation
    # ------------------------------------------------------------------
    def __post_init__(self):
        if not getattr(self, "__skip_type_validation__", False):
            self.validate_types()

    def _validate_date(self, field: Field):
        ftype = field.type
        is_date_field = (
            ftype is date or
            (get_origin(ftype) is Optional and get_args(ftype)[0] is date)
        )

        if is_date_field:
            if val := getattr(self, field.name, None):
                if isinstance(val, str):
                    parsed = DateParser(val)
                    object.__setattr__(self, field.name, parsed)
                    return True
        return False
    # ------------------------------------------------------------------
    #  Public helpers
    # ------------------------------------------------------------------
    def validate_types(self) -> None:
        """Raise :class:`TypeError` if any field value violates its annotation.

        * ``None`` always passes – honours ``Optional`` / ``| None``.
        * Containers typed as :class:`RelationshipList[T]` or ``list[T]`` are
          recursively checked.
        * Unrecognised / overly complex annotations fall back to *pass* in
          order to keep the implementation minimal.
        """
        for f in fields(self):
            expected = f.type
            value = getattr(self, f.name)
            origin = get_origin(expected)

            # Allow None regardless of annotation – covers Optional/Union
            if value is None:
                continue

            if self._validate_date(f):
                continue

            # 1️⃣ If someone annotated `list[SomeDC]` instead of `RelationshipList[SomeDC]`
            if origin is list:
                (elem_type,) = get_args(expected) or (Any,)
                if isinstance(elem_type, type) and issubclass(elem_type, BaseDataclass):
                    raise TypeError(
                        f"{self.__class__.__name__}.{f.name}: "
                        f"Annotated as `list[{elem_type.__name__}]` but must use "
                        f"`RelationshipList[{elem_type.__name__}]` for dataclass relationships."
                    )

            # 2️⃣ RelationshipList[T] must only be used for dataclass relationships.
            #     Only enforce if elem_type is a real Python type (skip forward‐refs/strings).
            if origin is RelationshipList:
                (elem_type,) = get_args(expected) or (Any,)
                if isinstance(elem_type, type) and not issubclass(elem_type, BaseDataclass):
                    raise TypeError(
                        f"{self.__class__.__name__}.{f.name}: "
                        f"Annotated as `RelationshipList[{elem_type.__name__}]` "
                        f"but `{elem_type.__name__}` is not a BaseDataclass—"
                        f"use plain `list[{elem_type.__name__}]` instead."
                    )

            if not self._matches_type(value, expected):
                raise TypeError(
                    f"{self.__class__.__name__}.{f.name} = {value!r} does not match "
                    f"declared type {f.type}"
                )

    # ------------------------------------------------------------------
    #  Class‑level relationship introspection (mirrors ORM helper)
    # ------------------------------------------------------------------
    @classmethod
    def relationship_fields(cls) -> dict[str, type | ForwardRef]:
        """
        Return a mapping of RelationshipList fields to their element type.
        Supports forward-referenced annotation strings by using get_type_hints.
        """
        rels: dict[str, type | ForwardRef] = {}
        # Resolve forward-refs in this class’s annotations
        hints = get_type_hints(cls, include_extras=True)
        for name, hint in hints.items():
            if get_origin(hint) is RelationshipList:
                (elem_type,) = get_args(hint) or (Any,)
                rels[name] = elem_type
        return rels
    # ------------------------------------------------------------------
    #  Internal recursive type matcher
    # ------------------------------------------------------------------
    @classmethod
    def _matches_type(cls, value: Any, expected: Any) -> bool:
        """Return *True* if *value* conforms to *expected* annotation.

        Handles a pragmatic subset of typing constructs used in domain models.
        """
        origin = get_origin(expected)

        # -------------------------------------------------- Optional / Union
        if origin in {Union, UnionType}:
            return any(cls._matches_type(value, arg) for arg in get_args(expected))

        # -------------------------------------------------- RelationshipList[T]
        if origin is RelationshipList:
            if not isinstance(value, list):
                return False
            (elem_type,) = get_args(expected) or (Any,)
            return all(cls._matches_type(v, elem_type) for v in value)

        # -------------------------------------------------- list[T]
        if origin is list:
            if not isinstance(value, list):
                return False
            (elem_type,) = get_args(expected) or (Any,)
            return all(cls._matches_type(v, elem_type) for v in value)

        # -------------------------------------------------- plain class or builtin
        if expected is UUIDStr:
            try:
                UUIDStr(value)
                return True
            except Exception:
                return False

        if isinstance(expected, type):
            return isinstance(value, expected)

        # -------------------------------------------------- fallback – assume OK
        return True

    @classmethod
    def _register_store(cls, store):
        cls._store = store

    @classmethod
    def get_pk(cls):
        return cls._pk
