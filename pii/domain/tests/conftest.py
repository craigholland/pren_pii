import pytest

from pii.domain.base.stores.person import PersonStore_NoDB
from pii.domain.base.stores.organization import OrganizationStore_NoDB
from pii.domain.base.stores.roles import (
    PersonRoleStore_NoDB,
    OrganizationRoleStore_NoDB,
    SystemRoleStore_NoDB,
)

@pytest.fixture(autouse=True)
def clear_domain_stores():
    """Reset all in-memory stores before each test."""
    PersonStore_NoDB._store.clear()
    OrganizationStore_NoDB._store.clear()
    PersonRoleStore_NoDB._store.clear()
    OrganizationRoleStore_NoDB._store.clear()
    SystemRoleStore_NoDB._store.clear()
