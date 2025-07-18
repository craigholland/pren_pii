import threading
import uuid
from dataclasses import dataclass
from typing import Optional, Dict, Callable, Any, Set, TypeAlias

from pii.database.permissions.exceptions import AccessDenied
from pii.database.permissions.system import ActAsSystem
from pii.database.permissions.user import UserPermissionInfo, UserRole

PermissionCheckerConstructor: TypeAlias = Callable[..., Any]
ThreadID: TypeAlias = int
ResourceID: TypeAlias = str


@dataclass
class AuditData:
    message: str
    permission_string: str
    resource_id: str
    result: bool


def disabled_checker_constructor():
    from pii.database.permissions.permissions_checker import PermissionChecker

    class DisabledChecker(PermissionChecker):
        def check_permission(self, person_id, role_id, requested, resource_id):
            return True

        def get_resources_by_permission_name(self, name):
            return []

    return DisabledChecker()


class ThreadLocalPermissionMeta(type):
    """
    Metaclass that manages thread-local PermissionController sessions.
    Ensures isolation of permission checks per thread.
    """

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls.sessions: Dict[ThreadID, PermissionController] = {}
        cls._lock = threading.Lock()
        cls.stored_sessions: Dict[ThreadID, list[PermissionController]] = {}
        cls.audit_trails: Dict[ThreadID, list[AuditData]] = {}
        cls._permission_checker_constructor: Optional[PermissionCheckerConstructor] = None
        cls._permission_checker_args = ()
        cls._permission_checker_kwargs = {}
        cls.no_commit_mode = False
        cls.default_app_name = ""

    def register_permission_checker_constructor(cls, func: PermissionCheckerConstructor, *args, **kwargs):
        cls._permission_checker_constructor = func
        cls._permission_checker_args = args
        cls._permission_checker_kwargs = kwargs

    def disable_permission_checks(cls):
        cls.register_permission_checker_constructor(disabled_checker_constructor)

    @property
    def session(cls) -> "PermissionController":
        ident = threading.current_thread().ident
        if ident not in cls.sessions:
            cls.setup_session(ident)
        return cls.sessions[ident]

    def setup_session(cls, ident: ThreadID):
        with cls._lock:
            cls.stored_sessions.setdefault(ident, [])
            cls.audit_trails.setdefault(ident, [])

            if cls._permission_checker_constructor is None:
                raise RuntimeError("Permission checker constructor not registered.")

            checker = cls._permission_checker_constructor(
                *cls._permission_checker_args, **cls._permission_checker_kwargs
            )
            cls.sessions[ident] = PermissionController(ident, checker)

    def push_session(cls):
        ident = threading.current_thread().ident
        current = cls.session
        cls.stored_sessions[ident].append(current)

        checker = cls._permission_checker_constructor(
            *cls._permission_checker_args, **cls._permission_checker_kwargs
        )
        cls.sessions[ident] = PermissionController(ident, checker)

    def pop_session(cls):
        ident = threading.current_thread().ident
        if not cls.stored_sessions.get(ident):
            raise RuntimeError("No stored session to pop for this thread.")
        cls.sessions[ident] = cls.stored_sessions[ident].pop()

    def clear_session_stack(cls):
        ident = threading.current_thread().ident
        cls.stored_sessions.get(ident, []).clear()
        cls.setup_session(ident)


class PermissionController(metaclass=ThreadLocalPermissionMeta):
    """
    Manages the active permission context for the current thread.
    Do not instantiate directly — always access via PermissionController.session
    """

    def __init__(self, ident: ThreadID, checker: Any):
        self.__strict = False
        self.__user_id = ""
        self.__acting_as_role_id = ""
        self.__language_override = None
        self.__user_info: Optional[UserPermissionInfo] = None
        self.__audit_trail: list[AuditData] = []
        self.session_id = str(uuid.uuid4())
        self.add_audit_event(f"Creating session: {self.session_id}")

        self.checker = checker
        self.account_recovery = False
        self.in_check = False
        self.resources_requested: Dict[ResourceID, Set[str]] = {}
        self.__in_final_check = False
        self.containing_action = ""
        self.delayed_checking = True
        self.skip_final_checks = False
        self.cache = {}
        self.app_name = self.default_app_name
        self.allowed_calls = None

    @property
    def user_id(self) -> str:
        return self.__user_id

    @user_id.setter
    def user_id(self, value: str):
        self.add_audit_event(f"Acting as user: {value}")
        self.__user_id = value

    @property
    def acting_as_role_id(self) -> str:
        return self.__acting_as_role_id

    @acting_as_role_id.setter
    def acting_as_role_id(self, value: str):
        self.add_audit_event(f"Acting as user role: {value}")
        self.__acting_as_role_id = value

    @property
    def language_override(self) -> Optional[str]:
        return self.__language_override

    @language_override.setter
    def language_override(self, value: Optional[str]):
        self.add_audit_event(f"Language override: {value}")
        self.__language_override = value

    def add_audit_event(self, message: str, permission_string: str = "", resource_id: str = "", result: bool = False):
        self.__audit_trail.append(AuditData(
            message=message,
            permission_string=permission_string,
            resource_id=resource_id,
            result=result,
        ))

    def log_audit_messages(self):
        # Optional logging hook — no-op for now
        pass

    def print_audit_trail(self):
        print("\n*****   RESPONSE AUDIT TRAIL   *****")
        for entry in self.__audit_trail:
            print(entry)
        print("***** END RESPONSE AUDIT TRAIL *****\n")

    @property
    def in_final_check(self) -> bool:
        return self.__in_final_check

    def setup_user(
        self,
        user_id: str,
        act_as_role_id: Optional[str] = None,
        location_id: Optional[str] = None,
        device_id: Optional[str] = None,
        language_override: Optional[str] = None,
        user_permission_info: Optional[UserPermissionInfo] = None
    ):
        self.user_id = user_id
        self.acting_as_role_id = act_as_role_id or ""
        self.language_override = language_override

        # Use provided permission info or construct a basic one
        if user_permission_info:
            self.__user_info = user_permission_info
        else:
            self.__user_info = UserPermissionInfo(
                user_id=user_id,
                roles=[UserRole(id=act_as_role_id or "default", name="(unspecified)")],
                permissions=set()
            )

    def must_have_permission(self, permission: str, resource: str):
        if not self.does_user_have_permission(resource, permission):
            raise AccessDenied("You do not have the required permission for the resource")

    def does_user_have_permission(self, resource_id: ResourceID, permission_name: str, p_user_id: Optional[str] = None) -> bool:
        if not self.__in_final_check:
            return self.__does_user_have_permission(resource_id, permission_name, p_user_id)
        return False

    def __does_user_have_permission(self, resource_id: ResourceID, permission_name: str, p_user_id: Optional[str]) -> bool:
        if not resource_id or self.__in_final_check or not self.delayed_checking:
            result = self.checker.check_permission(
                p_user_id or self.__user_id,
                self.__acting_as_role_id,
                permission_name,
                resource_id,
            )
            self.add_audit_event(
                f"Check Access '{permission_name}' for user_id={p_user_id or self.user_id} to resource={resource_id}",
                permission_string=permission_name,
                resource_id=resource_id,
                result=result,
            )
        else:
            self.resources_requested.setdefault(resource_id, set()).add(permission_name)
            result = True
        return result

    def final_check(self, session):
        with ActAsSystem("Check Permissions", session):
            self.__in_final_check = True

            if not self.skip_final_checks:
                for resource_id, perms in self.resources_requested.items():
                    for perm in perms:
                        if not self.__does_user_have_permission(resource_id, perm, None):
                            raise AccessDenied(f"Permission: {perm}, Resource: {resource_id}")

            self.log_audit_messages()
            self.__in_final_check = False

    def user_has_permission(self, permission_name: str, user_id: Optional[str] = None) -> bool:
        return self.checker.check_permission(
            user_id or self.__user_id,
            self.__acting_as_role_id,
            permission_name,
            None
        )

    def has_permission_name(self, permission_name: str) -> bool:
        return permission_name in (self.__user_info.permissions if self.__user_info else set())
