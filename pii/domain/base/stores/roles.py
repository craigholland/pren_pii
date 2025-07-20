from pii.common.abstracts.base_store_nodb import BaseStore_NoDB
from pii.domain.base.dataclasses import (
    PersonRole, OrganizationRole, SystemRole
)

class PersonRoleStore_NoDB(BaseStore_NoDB):
    """
    In-memory store for PersonRole entities.
    """
    _dc_model = PersonRole

class OrganizationRoleStore_NoDB(BaseStore_NoDB):
    """
    In-memory store for OrgRole entities.
    """
    _dc_model = OrganizationRole

class SystemRoleStore_NoDB(BaseStore_NoDB):
    """
    In-memory store for SystemRole entities.
    """
    _dc_model = SystemRole