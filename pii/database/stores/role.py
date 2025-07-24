from pii.database.store_adapters.sqlalchemy_store import BaseStoreSQLAlchemy
from typing import TypeVar

from pii.database.models.roles import PartyRole, OrganizationRole, SystemRole, PersonRole


T = TypeVar('T')
class PartyRoleStore(BaseStoreSQLAlchemy):
    """
    DB-based store for PartyRole entities.
    """
    _orm_model = PartyRole
    def __init__(self):
        super().__init__()


class PersonRoleStore(BaseStoreSQLAlchemy):
    """
    DB-based store for PersonRole entities.
    """
    _orm_model = PersonRole
    def __init__(self):
        super().__init__()


class OrganizationRoleStore(BaseStoreSQLAlchemy):
    """
    DB-based store for OrgRole entities.
    """
    _orm_model = OrganizationRole

class SystemRoleStore(BaseStoreSQLAlchemy):
    """
    DB-based store for SystemRole entities.
    """
    _orm_model = SystemRole