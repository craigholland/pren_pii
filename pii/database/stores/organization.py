from pii.database.store_adapters.sqlalchemy_store import BaseStoreSQLAlchemy
from typing import Any, Optional, TypeVar

from pii.database.models.party import Organization


T = TypeVar('T')

class OrganizationStore(BaseStoreSQLAlchemy):
    _orm_model = Organization

    def __init__(self):
        super().__init__()