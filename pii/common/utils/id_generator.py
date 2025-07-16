import uuid

def generate_uuid() -> uuid.UUID:
    """Return a new random UUID."""
    return uuid.uuid4()
