import pytest
from uuid import UUID
from pii.common.utils.uuid_str import uuid_str, UUIDStr
from pii.common.utils.classproperty import classproperty


def test_uuid_str_valid_uuid_string():
    """uuid_str should accept a valid UUID string and return it."""
    valid = "550e8400-e29b-41d4-a716-446655440000"
    result = uuid_str(valid)
    assert isinstance(result, str)
    assert result == valid


def test_uuid_str_uuid_object():
    """uuid_str should accept a UUID object and return its string form."""
    u = UUID("550e8400-e29b-41d4-a716-446655440000")
    result = uuid_str(u)
    assert isinstance(result, str)
    assert result == str(u)


def test_uuid_str_empty_and_none_okay():
    """By default, empty string and None are allowed."""
    assert uuid_str("", allow_empty_str=True) == ""
    assert uuid_str(None, allow_None=True) is None


def test_uuid_str_invalid_string_raises_value_error():
    """uuid_str should reject malformed UUID strings."""
    with pytest.raises(ValueError):
        uuid_str("not-a-valid-uuid")


def test_uuid_str_non_string_non_uuid_raises_type_error():
    """uuid_str should reject unsupported types with TypeError."""
    with pytest.raises(TypeError):
        uuid_str(12345)  # neither str nor UUID


def test_UUIDStr_validates_on_creation():
    """UUIDStr should only allow valid UUID strings."""
    valid = "550e8400-e29b-41d4-a716-446655440000"
    s = UUIDStr(valid)
    assert isinstance(s, str)
    assert s == valid


def test_UUIDStr_rejects_invalid():
    """UUIDStr must raise ValueError for invalid UUIDs."""
    with pytest.raises(ValueError):
        UUIDStr("invalid-uuid")


def test_classproperty_decorator():
    """@classproperty should expose a read-only property on both class and instance."""
    class Dummy:
        _x = 123

        @classproperty
        def x(cls):
            return cls._x + 1

    # Access on class
    assert Dummy.x == 124
    # Access on instance
    inst = Dummy()
    assert inst.x == 124


