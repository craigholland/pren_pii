import uuid


def uuid_str(value, allow_None=True, allow_empty_str=True, raise_exc=True):
    if value is None and allow_None or value == "" and allow_empty_str:
        return value

    if isinstance(value, str):
        try:
            value = uuid.UUID(value)  # ensures it's a valid UUID string
        except ValueError:
            if raise_exc:
                raise ValueError(f"Invalid UUID string: {value}")
            return None

    if isinstance(value, uuid.UUID):
        value = str(value)

    if isinstance(value, str):
        return value

    if raise_exc:
        raise TypeError(f"id must be a UUID or a valid UUID string, got {value} ({type(value)})")
    return None