import uuid
from contextlib import AbstractContextManager
from pii.database.permissions.controller import PermissionController
from sqlalchemy.orm import Session


class ActAsUser(AbstractContextManager):
    """
    Context manager to temporarily act as another user with a given role.
    Ensures permission state is isolated and SQLAlchemy objects are expired.
    """

    def __init__(self, reason: str, db_session: Session, user_id: str, role_id: str):
        self.reason = reason
        self.id = str(uuid.uuid4())
        self.db_session = db_session
        self.user_id = user_id
        self.role_id = role_id
        self.initial_user_id: str = PermissionController.session.user_id

    def __enter__(self) -> str:
        PermissionController.push_session()
        PermissionController.session.user_id = self.user_id
        PermissionController.session.acting_as_role_id = self.role_id
        self.db_session.expire_all()
        return self.initial_user_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        PermissionController.session.add_audit_event(
            f"ActingAsUser({self.id}): Exiting"
        )
        PermissionController.pop_session()
        self.db_session.expire_all()


class ActAsSystem(ActAsUser):
    def __init__(self, reason: str, db_session: Session):
        super().__init__(reason, db_session, "System", "SystemRole")
