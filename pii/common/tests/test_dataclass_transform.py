import pytest
import json
from datetime import datetime
from uuid import uuid4, UUID

from pii.common.utils.dataclass_transformer import DataclassTransformer
from pii.common.tests.conftest import Inner, Outer


def test_import_from_dict(sample_uuid, iso_time):
    """DataclassTransformer.import_ should build primitives, nested dataclasses, and list fields."""
    data = {
        "id": str(sample_uuid),
        "timestamp": iso_time,
        "value": "42.5",
        "flag": True,
        "inner": {"id": str(sample_uuid), "name": "inner"},
        "tags": ["a", "b"],
        "metadata": {"x": "1", "y": "2"},
        "nested_list": [{"id": str(sample_uuid), "name": "child"}]
    }
    t = DataclassTransformer(Outer)
    t.import_(data)
    dc = t.as_dataclass

    # ID coerced to string
    assert dc.id == str(sample_uuid)
    # Timestamp parsed to datetime
    assert isinstance(dc.timestamp, datetime)
    # Numeric coercion
    assert dc.value == 42.5
    # Boolean passed through
    assert dc.flag is True

    # Nested dataclass built
    assert isinstance(dc.inner, Inner)
    assert dc.inner.name == "inner"

    # Primitive list stays list[str]
    assert isinstance(dc.tags, list)
    assert dc.tags == ["a", "b"]

    # Dict values coerced to int
    assert dc.metadata == {"x": 1, "y": 2}

    # RelationshipList of Inner is built as list of Inner
    assert isinstance(dc.nested_list, list)
    assert isinstance(dc.nested_list[0], Inner)
    assert dc.nested_list[0].name == "child"


def test_import_from_json(sample_uuid, iso_time):
    """Importing from JSON string should behave identically to dict import."""
    payload = {
        "id": str(sample_uuid),
        "timestamp": iso_time,
        "value": 1.23,
        "flag": None,
        "inner": {"id": str(sample_uuid), "name": "json"},
        "tags": [],
        "metadata": {"score": "10"},
        "nested_list": [{"id": str(sample_uuid), "name": "nested"}]
    }
    json_data = json.dumps(payload)

    t = DataclassTransformer(Outer)
    t.import_(json_data)
    dc = t.as_dataclass

    assert isinstance(dc, Outer)
    assert dc.id == str(sample_uuid)
    assert dc.flag is None
    assert dc.metadata["score"] == 10

    # Nested list built into Inner instances
    assert isinstance(dc.nested_list, list)
    assert isinstance(dc.nested_list[0], Inner)
    assert dc.nested_list[0].name == "nested"


def test_patch_existing_instance(sample_uuid):
    """Patching an existing dataclass instance should update only specified fields."""
    base = Outer(
        id=sample_uuid,
        timestamp=datetime.now(),
        value=0.0,
        flag=False,
        inner=Inner(id=sample_uuid, name="base"),
        tags=[],
        metadata={},
        nested_list=[]
    )
    patch = {
        "value": 99.99,
        "inner": {"name": "patched"},
        "tags": ["updated"],
        "metadata": {"a": "5"},
        "nested_list": [{"id": str(sample_uuid), "name": "patched-child"}]
    }
    t = DataclassTransformer(base)
    t.import_(patch)
    dc = t.as_dataclass

    assert dc.value == 99.99
    # Inner gets patched in place
    assert isinstance(dc.inner, Inner)
    assert dc.inner.name == "patched"
    # Other fields
    assert dc.tags == ["updated"]
    assert dc.metadata["a"] == 5
    # Nested list replaced
    assert isinstance(dc.nested_list[0], Inner)
    assert dc.nested_list[0].name == "patched-child"


def test_as_dict_and_json(sample_uuid, iso_time):
    """Exporting a fully-built dataclass to dict/JSON should include all fields."""
    data = {
        "id": str(sample_uuid),
        "timestamp": iso_time,
        "value": 10.1,
        "flag": False,
        "inner": {"id": str(sample_uuid), "name": "dict"},
        "tags": ["dict"],
        "metadata": {"z": "99"},
        "nested_list": []
    }
    t = DataclassTransformer(Outer)
    t.import_(data)
    out_dict = t.as_dict
    out_json = t.as_json

    # Basic dict structure
    assert isinstance(out_dict, dict)
    assert out_dict["id"] == str(sample_uuid)
    assert isinstance(out_dict["inner"], dict)
    assert "timestamp" in out_dict

    # JSON contains timestamp key
    assert '"timestamp"' in out_json


def test_type_errors():
    """Invalid initializers or import inputs must raise TypeError/ValueError appropriately."""
    # Bad initializer
    with pytest.raises(TypeError):
        DataclassTransformer("not_a_dataclass")

    t = DataclassTransformer(Outer)
    # Unsupported type
    with pytest.raises(TypeError):
        t.import_(1234)

    # Valid JSON but not a dict
    with pytest.raises(TypeError):
        t.import_("[1, 2, 3]")


def test_import_dataclass_instance(sample_uuid, iso_time):
    """Importing an existing dataclass instance should return the same object."""
    base = Outer(
        id=sample_uuid,
        timestamp=datetime.fromisoformat(iso_time),
        value=5.0,
        flag=True,
        inner=Inner(id=sample_uuid, name="orig"),
        tags=["t"],
        metadata={"m": 1},
        nested_list=[Inner(id=sample_uuid, name="child")],
    )
    t = DataclassTransformer(base)
    result = t.import_(base).as_dataclass
    assert result is base


def test_get_dataclass_helper():
    """get_dataclass should resolve dataclass types and instances."""
    assert DataclassTransformer.get_dataclass(Inner) is Inner
    inst = Inner(id=str(uuid4()), name="x")
    assert DataclassTransformer.get_dataclass(inst) is Inner
    assert DataclassTransformer.get_dataclass(123) is None


def test_import_chaining_with_patch(sample_uuid):
    """import_ returns self when patching an existing instance, allowing chaining."""
    base = Outer(
        id=sample_uuid,
        timestamp=datetime.now(),
        value=1.0,
        flag=True,
        inner=Inner(id=sample_uuid, name="start"),
        tags=[],
        metadata={},
        nested_list=[]
    )
    transformer = DataclassTransformer(base)
    returned = transformer.import_({"value": 2.0})
    assert returned is transformer
    assert transformer.as_dataclass.value == 2.0


def test_invalid_and_non_dict_json():
    """Malformed JSON raises ValueError; JSON list raises TypeError."""
    t = DataclassTransformer(Outer)
    with pytest.raises(ValueError):
        t.import_('{"bad_json": ')
    with pytest.raises(TypeError):
        t.import_('[1, 2, 3]')


def test_deep_nested_patch(sample_uuid):
    """Patching multiple nested elements in a RelationshipList should apply correctly."""
    inner1 = Inner(id=sample_uuid, name="A")
    inner2 = Inner(id=sample_uuid, name="B")
    base = Outer(
        id=sample_uuid,
        timestamp=datetime.now(),
        value=0.0,
        flag=True,
        inner=inner1,
        tags=[],
        metadata={},
        nested_list=[inner1, inner2]
    )
    patch = {
        "nested_list": [
            {"name": "X"},
            {"name": "Y"}
        ]
    }
    DataclassTransformer(base).import_(patch)
    assert base.nested_list[0].name == "X"
    assert base.nested_list[1].name == "Y"
