from sqlalchemy import event
from pii.database.models.core.service_object import ServiceObject

@event.listens_for(ServiceObject, "before_insert", propagate=True)
@event.listens_for(ServiceObject, "before_update", propagate=True)
def validate_before_write(mapper, connection, target):
    if hasattr(target, "validate"):
        target.validate()
