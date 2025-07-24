from pii.database.store_adapters.sqlalchemy_store import BaseStoreSQLAlchemy
from typing import Any, Optional, TypeVar

from pii.database.models.party import Person, Party


T = TypeVar('T')

class PartyStore(BaseStoreSQLAlchemy):
    _orm_model = Party

    def __init__(self):
        super().__init__()

class PersonStore(BaseStoreSQLAlchemy):
    _orm_model = Person

    def __init__(self):
        super().__init__()