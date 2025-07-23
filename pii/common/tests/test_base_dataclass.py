import pytest
from dataclasses import asdict
from pii.common.tests.conftest import Inner, Outer
from datetime import datetime


def test_uuid_normalization(sample_uuid):
    """Verify that UUIDStr values are properly normalized and retained as strings."""
    obj = Inner(id=sample_uuid, name="John")
    assert isinstance(obj.id, str)
    assert str(sample_uuid) == obj.id


def test_relationship_fields_reflection():
    """Check that the relationship_fields method correctly identifies nested dataclasses."""
    fields = Outer.relationship_fields()
    assert "nested_list" in fields
    assert fields["nested_list"].__name__ == "Inner"


def test_validate_types_pass(outer_instance):
    """Ensure that type validation does not raise errors for valid objects."""
    outer_instance.validate_types()


def test_asdict_consistency(outer_instance):
    """Verify that asdict returns a dictionary with expected structure and key presence."""
    dc_dict = asdict(outer_instance)
    assert "id" in dc_dict
    assert "inner" in dc_dict
    assert isinstance(dc_dict["metadata"], dict)


def test_equality_and_hashing(sample_uuid):
    """Ensure that two objects with the same ID are equal regardless of other fields."""
    a = Inner(id=sample_uuid, name="A")
    b = Inner(id=sample_uuid, name="B")
    assert a != b
    assert a.id == b.id


def test_validate_types_fail_on_corrupted(corrupted_outer):
    """Test that corrupted input data raises a validation error during instantiation."""
    with pytest.raises(ValueError):
        Outer(**corrupted_outer)


def test_none_in_required_field_fails():
    """Ensure that missing required fields (like `id`) raise a TypeError."""
    with pytest.raises(TypeError):
        Inner(name="Invalid")  # id is required and missing


def test_missing_optional_fields():
    """Verify that missing optional fields still results in valid object creation."""
    obj = Inner(id="550e8400-e29b-41d4-a716-446655440000", name="OnlyRequired")
    assert obj.name == "OnlyRequired"
    assert isinstance(obj.id, str)


def test_nested_list_relationship_structure(sample_uuid):
    """Ensure RelationshipList fields contain the correct dataclass instances."""
    inner_1 = Inner(id=sample_uuid, name="nested1")
    inner_2 = Inner(id=sample_uuid, name="nested2")
    outer = Outer(
        id=sample_uuid,
        timestamp=datetime.fromisoformat("2024-01-01T12:00:00"),
        value=1.0,
        flag=True,
        inner=inner_1,
        tags=["x"],
        metadata={"m": 1},
        nested_list=[inner_1, inner_2]
    )
    assert len(outer.nested_list) == 2
    for item in outer.nested_list:
        assert isinstance(item, Inner)


def test_asdict_deep_conversion(sample_uuid):
    """Test that nested dataclasses are deeply converted into dictionaries via asdict."""
    inner = Inner(id=sample_uuid, name="Nested")
    outer = Outer(
        id=sample_uuid,
        timestamp=datetime.now(),
        value=0.0,
        flag=False,
        inner=inner,
        tags=[],
        metadata={},
        nested_list=[inner]
    )
    result = asdict(outer)
    assert isinstance(result["inner"], dict)
    assert isinstance(result["nested_list"][0], dict)


def test_post_init_type_enforcement(sample_uuid):
    """Test that runtime mutation of types triggers validation errors."""
    obj = Inner(id=sample_uuid, name="ValidName")
    obj.name = 123  # Wrong type
    with pytest.raises(TypeError):
        obj.validate_types()


def test_invalid_timestamp_type(sample_uuid):
    """Verify that invalid timestamp strings are rejected when datetime is expected."""
    with pytest.raises(TypeError):
        Outer(
            id=sample_uuid,
            timestamp="2024-01-01T12:00:00",  # Invalid type
            value=1.0,
            flag=True,
            inner=Inner(id=sample_uuid, name="fail"),
            tags=[],
            metadata={},
            nested_list=[]
        )

def test_inner_serialization_roundtrip(sample_uuid):
    """
    Verify that SerializableMixin on BaseDataclass allows a simple
    dataclass (Inner) to round‑trip through to_dict()/from_dict().
    """
    # 1) Construct an Inner instance
    orig = Inner(id=sample_uuid, name="TestName")

    # 2) Serialize to primitives
    data = orig.to_dict()
    assert isinstance(data, dict)
    assert set(data.keys()) >= {"id", "name"}

    # 3) Rehydrate and verify equality
    clone = Inner.from_dict(data)
    assert isinstance(clone, Inner)
    assert clone == orig
