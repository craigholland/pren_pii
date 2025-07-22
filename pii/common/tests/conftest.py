import pytest
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from uuid import uuid4

from pii.common.abstracts.base_dataclass import BaseDataclass, RelationshipList
from pii.common.utils.uuid_str import UUIDStr

# ------------------------
# Test Dataclasses
# ------------------------

@dataclass
class Inner(BaseDataclass):
    """Simple dataclass with a UUIDStr ID and a name field."""
    id: UUIDStr
    name: str


@dataclass
class Outer(BaseDataclass):
    """Nested dataclass that includes primitives and relationship fields."""
    id: Optional[UUIDStr]
    timestamp: datetime
    value: float
    flag: Optional[bool]
    inner: Inner
    tags: List[str]
    metadata: Dict[str, int]
    nested_list: RelationshipList[Inner]

# ------------------------
# Fixtures: Valid Instances
# ------------------------

@pytest.fixture
def sample_uuid():
    """Returns a random UUID for use in test inputs."""
    return uuid4()


@pytest.fixture
def iso_time():
    """Returns a current ISO8601 datetime string."""
    return datetime.now().isoformat()


@pytest.fixture
def inner_instance(sample_uuid):
    """Returns a valid Inner instance."""
    return Inner(id=sample_uuid, name="sample inner")


@pytest.fixture
def outer_instance(sample_uuid, inner_instance):
    """Returns a valid Outer instance."""
    return Outer(
        id=sample_uuid,
        timestamp=datetime.now(),
        value=42.0,
        flag=True,
        inner=inner_instance,
        tags=['tag1', 'tag2'],
        metadata={"a": 1, "b": 2},
        nested_list=[inner_instance]
    )

# ------------------------
# Fixtures: Corrupted Instances
# ------------------------

@pytest.fixture
def corrupted_inner():
    """Returns a dict that would fail UUID validation in Inner."""
    return {"id": "not-a-uuid", "name": 1234}  # name should be str


@pytest.fixture
def corrupted_outer(corrupted_inner):
    """Returns a dict that would fail multiple field validations in Outer."""
    return {
        "id": "123-invalid-uuid",
        "timestamp": "not-a-datetime",
        "value": "not-a-float",
        "flag": "not-a-bool",
        "inner": corrupted_inner,
        "tags": "should-be-a-list",
        "metadata": {"x": "not-an-int"},
        "nested_list": [corrupted_inner]
    }
