import pytest
from datetime import datetime

from dataclasses import asdict, is_dataclass
from uuid import uuid4

from pii.common.abstracts.base_store_nodb import BaseStore_NoDB
from pii.common.tests.conftest import Outer, Inner


class OuterStore(BaseStore_NoDB):
    _dc_model = Outer
    def __init__(self):
        super().__init__(Outer)


@pytest.fixture
def store():
    return OuterStore()


def test_insert_and_get(store, outer_instance):
    """Test that a new record can be inserted and retrieved by ID."""
    inserted = store.put(outer_instance)
    retrieved = store.get(inserted.id)
    assert retrieved == inserted
    assert retrieved.inner == outer_instance.inner


def test_patch_existing_record(store, outer_instance):
    """Test that patching an existing record updates only specified fields."""
    store.put(outer_instance)
    outer_instance.value = 999.0
    updated = store.put(outer_instance)
    assert updated.value == 999.0


def test_update_existing_record(store, outer_instance):
    """Test full update of a record using 'put()' with an existing ID."""
    outer_instance.value = 3.14
    store.put(outer_instance)
    outer_instance.value = 6.28
    result = store.put(outer_instance)
    assert result.value == 6.28


def test_all_returns_all_records(store, outer_instance):
    """Test that 'all()' returns all stored dataclass records."""
    store.put(outer_instance)
    records = store.all()
    assert len(records) == 1
    assert records[0].id == outer_instance.id


def test_delete_by_id(store, outer_instance):
    """Test that a record can be deleted by ID."""
    store.put(outer_instance)
    store.delete(outer_instance.id)
    assert store.get(outer_instance.id) is None


def test_from_dict_converts_dict_to_dataclass(store, outer_instance):
    """Test 'from_dict()' recreates a dataclass instance from a dictionary."""
    data = asdict(outer_instance)
    reconstructed = store.from_dict(data)
    assert is_dataclass(reconstructed)
    assert reconstructed.id == outer_instance.id
    assert reconstructed.inner.name == outer_instance.inner.name


def test_insert_nested_list_relationship(store, sample_uuid):
    """Test inserting a dataclass with a list of nested dataclasses."""
    inner1 = Inner(id=uuid4(), name="A")
    inner2 = Inner(id=uuid4(), name="B")
    outer = Outer(
        id=sample_uuid,
        timestamp=datetime.fromisoformat("2024-01-01T00:00:00"),
        value=1.0,
        flag=True,
        inner=inner1,
        tags=["x", "y"],
        metadata={"x": 1},
        nested_list=[inner1, inner2]
    )
    stored = store.put(outer)
    assert len(stored.nested_list) == 2
    assert all(isinstance(i, Inner) for i in stored.nested_list)


def test_put_invalid_type_raises(store):
    """Test that putting a non-dataclass raises TypeError."""
    with pytest.raises(TypeError):
        store.put({"id": "invalid", "value": 123})


def test_delete_nonexistent_id_is_safe(store):
    """Test that deleting a non-existent ID does not raise error."""
    try:
        store.delete("nonexistent-id")
    except Exception as e:
        pytest.fail(f"Unexpected exception raised: {e}")
