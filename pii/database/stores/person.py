from pii.database.store_adapters.sqlalchemy_store import BaseStoreSQLAlchemy
from typing import Any, Optional, TypeVar

from pii.database.models.party import Person


T = TypeVar('T')

class PersonStore(BaseStoreSQLAlchemy):
    _orm_model = Person

    def __init__(self):
        super().__init__()