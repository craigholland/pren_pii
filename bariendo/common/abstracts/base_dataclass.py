from dataclasses import fields
from types import UnionType
from typing import (
    Any, Generic, TypeVar, ClassVar, get_args, get_origin, Union)

from bariendo.common.utils.uuid_str import uuid_str

"""Common base mix‑in for domain dataclasses.

Features
--------
* **UUID primary‑key normalisation** – any attribute named ``id`` (or the
  value of :pyattr:`_pk`) is coerced to a canonical UUID string via
  :pyfunc:`bariendo.common.utils.uuid_str.uuid_str` every time it is
  assigned.
* **Automatic runtime type‑checking** on construction (``__post_init__``)
  and via :py:meth:`validate_types`. Static flag
  :pyattr:`__skip_type_validation__` allows per‑class opt‑out.
* **Relationship introspection** – :py:meth:`relationship_fields` mirrors the
  ORM‑side helper and returns a mapping of ``field_name → target dataclass``
  for all :pyclass:`~bariendo.common.typing.relationship.RelationshipList`
  fields.

Python 3.12 compliant – subclasses the plain ``list`` class rather than the
``list[T]`` generic alias.
"""


__all__ = ["BaseDataclass"]

T = TypeVar("T")

class RelationshipList(list, Generic[T]):
    """
        Identical to `list[T]`, but its *type* signals
        “this collection represents an ORM relationship”.
        No behaviour is changed.
        """
    __slots__ = ()

class BaseDataclass:
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

    # ------------------------------------------------------------------
    #  Automatic post‑init validation
    # ------------------------------------------------------------------
    def __post_init__(self):
        if not getattr(self, "__skip_type_validation__", False):
            self.validate_types()

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
            value = getattr(self, f.name)

            # Allow None regardless of annotation – covers Optional/Union
            if value is None:
                continue

            if not self._matches_type(value, f.type):
                raise TypeError(
                    f"{self.__class__.__name__}.{f.name} = {value!r} does not match "
                    f"declared type {f.type}"
                )

    # ------------------------------------------------------------------
    #  Class‑level relationship introspection (mirrors ORM helper)
    # ------------------------------------------------------------------
    @classmethod
    def relationship_fields(cls):
        """Return ``{ field_name: target_dataclass }`` for RelationshipList fields."""
        rels: dict[str, type] = {}
        for f in fields(cls):
            origin = get_origin(f.type)
            if origin is RelationshipList:
                (elem_type,) = get_args(f.type) or (Any,)
                rels[f.name] = elem_type
        return rels

    # ------------------------------------------------------------------
    #  Internal recursive type matcher
    # ------------------------------------------------------------------
    @classmethod
    def _matches_type(cls, value: Any, expected: Any) -> bool:  # noqa: C901 – a bit complex but contained
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
        if isinstance(expected, type):
            return isinstance(value, expected)

        # -------------------------------------------------- fallback – assume OK
        return True


    @classmethod
    def _register_store(cls, store):
        cls._store = store