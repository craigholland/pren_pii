import pytest
import json
from datetime import datetime
from pii.common.utils.dataclass_transformer import DataclassTransformer
from pii.common.tests.conftest import Inner, Outer

def test_import_from_dict(sample_uuid, iso_time):
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

    assert dc.id == str(sample_uuid)
    assert isinstance(dc.timestamp, datetime)
    assert dc.value == 42.5
    assert dc.flag is True
    assert dc.inner.name == "inner"
    assert dc.metadata["x"] == 1
    assert dc.nested_list[0].name == "child"


def test_import_from_json(sample_uuid, iso_time):
    json_data = json.dumps({
        "id": str(sample_uuid),
        "timestamp": iso_time,
        "value": 1.23,
        "flag": None,
        "inner": {"id": str(sample_uuid), "name": "json"},
        "tags": [],
        "metadata": {"score": "10"},
        "nested_list": [{"id": str(sample_uuid), "name": "nested"}]
    })
    t = DataclassTransformer(Outer)
    t.import_(json_data)

    assert t.as_dataclass.inner.name == "json"
    assert t.as_dataclass.flag is None
    assert t.as_dataclass.metadata["score"] == 10


def test_patch_existing_instance(sample_uuid):
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
    assert dc.inner.name == "patched"
    assert dc.tags == ["updated"]
    assert dc.metadata["a"] == 5
    assert dc.nested_list[0].name == "patched-child"


def test_as_dict_and_json(sample_uuid, iso_time):
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
    assert isinstance(t.as_dict, dict)
    assert "timestamp" in t.as_dict
    assert '"timestamp"' in t.as_json


def test_type_errors():
    with pytest.raises(TypeError):
        DataclassTransformer("not_a_dataclass")

    t = DataclassTransformer(Outer)
    with pytest.raises(TypeError):
        t.import_(1234)

    with pytest.raises(ValueError):
        t.import_("[1, 2, 3]")  # not a dict-style JSON
