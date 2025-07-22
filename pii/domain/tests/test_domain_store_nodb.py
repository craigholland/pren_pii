import pytest
from pii.domain.base.dataclasses import (
    Person,
    Organization,
    PersonRole,
    OrganizationRole,
    SystemRole,
)
from pii.domain.base.stores.person import PersonStore_NoDB
from pii.domain.base.stores.organization import OrganizationStore_NoDB
from pii.domain.base.stores.roles import (
    PersonRoleStore_NoDB,
    OrganizationRoleStore_NoDB,
    SystemRoleStore_NoDB,
)

@pytest.mark.parametrize(
    "StoreCls, DCcls",
    [
        (PersonStore_NoDB, Person),
        (OrganizationStore_NoDB, Organization),
        (PersonRoleStore_NoDB, PersonRole),
        (OrganizationRoleStore_NoDB, OrganizationRole),
        (SystemRoleStore_NoDB, SystemRole),
    ],
)
def test_put_get_all_delete_roundtrip(StoreCls, DCcls):
    """Each NoDB store should support put, get, all, and delete operations."""
    store = StoreCls()
    dc = DCcls()
    inserted = store.put(dc)
    pk = getattr(inserted, DCcls.get_pk())
    assert isinstance(pk, str) and pk

    assert store.get(pk) is inserted
    assert inserted in store.all()

    assert store.delete(pk) is True
    assert store.get(pk) is None
    assert store.delete(pk) is False

@pytest.mark.parametrize(
    "StoreCls, DCcls, patch_data, updated_field",
    [
        (PersonStore_NoDB, Person, {"name": "Patched"}, "name"),
        (OrganizationStore_NoDB, Organization, {"legal_name": "NewName"}, "legal_name"),
        (PersonRoleStore_NoDB, PersonRole, {"description": "Desc"}, "description"),
    ],
)
def test_patch_and_update(StoreCls, DCcls, patch_data, updated_field):
    """
    patch() should update only the specified fields,
    and put() with a full dataclass instance should replace the record.
    """
    store = StoreCls()
    dc = DCcls()
    inserted = store.put(dc)
    pk = getattr(inserted, DCcls.get_pk())

    patched = store.patch({DCcls.get_pk(): pk, **patch_data})
    assert getattr(patched, updated_field) == patch_data[updated_field]

    new_dc = DCcls(**{DCcls.get_pk(): pk, **patch_data})
    updated = store.put(new_dc)
    assert getattr(updated, updated_field) == patch_data[updated_field]

def test_from_dict_creates_dataclass_instance():
    """Store.from_dict should build a dataclass instance from a dict without saving."""
    store = PersonStore_NoDB()
    data = {"name": "FromDict"}
    dc = store.from_dict(data)
    assert isinstance(dc, Person)
    assert dc.name == "FromDict"
    assert dc.id is None

def test_dc_model_and_pk_field_properties():
    """Stores should expose classproperty dc_model and pk_field correctly."""
    ps = PersonStore_NoDB()
    assert ps.dc_model is Person
    assert ps.pk_field == Person.get_pk()
    # Class-level access works too
    assert PersonStore_NoDB.dc_model is Person
    assert PersonStore_NoDB.pk_field == "id"
