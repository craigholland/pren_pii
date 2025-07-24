from pii.database.store_adapters.sqlalchemy_store import BaseStoreSQLAlchemy
from typing import TypeVar

from pii.database.models.history import (
    PersonName,
    PersonGender,
    MaritalStatus
)


T = TypeVar('T')

class PersonNameStore(BaseStoreSQLAlchemy):
    """
    DB-based store for PersonName entities.
    """
    _orm_model = PersonName
    def __init__(self):
        super().__init__()


class PersonGenderStore(BaseStoreSQLAlchemy):
    """
    DB-based store for PersonGender entities.
    """
    _orm_model = PersonGender

class MaritalStatusStore(BaseStoreSQLAlchemy):
    """
    DB-based store for MaritalStatus entities.
    """
    _orm_model = MaritalStatus