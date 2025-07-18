from functools import wraps
from typing import Callable, Optional, Any, Union, Dict

from pii.database.permissions.controller import PermissionController
from pii.database.permissions.enums import PermissionType, PermissionTrigger
from pii.database.permissions.exceptions import AccessDenied

PermissionMapping = Dict[Union[PermissionType, str], Union[str, Callable]]


def restricted_resource(
    **permission_map: Union[str, Callable[[Any], str]]
):
    """
    Class-level decorator to attach permission metadata to ORM models.

    Usage:
        @resource(
            can_read="read_permission",
            can_update_field=my_custom_field_checker,
            get_resource_id=lambda obj: obj.id
        )
        class MyModel: ...

    :param permission_map: Mapping of permission types or triggers to permission names or functions
    """
    def decorator(cls):
        cls.__permission_map__ = {}

        for key, value in permission_map.items():
            if isinstance(key, str):
                try:
                    enum_key = PermissionType[key]
                except KeyError:
                    enum_key = key  # Allow custom non-enum keys
            else:
                enum_key = key
            cls.__permission_map__[enum_key] = value

        return cls

    return decorator


def permission_required(
    permission: PermissionType,
    trigger: Optional[PermissionTrigger] = None,
    get_resource_id: Optional[Callable[[Any], str]] = None,
):
    """
    Method-level decorator for service or model-level permission enforcement.

    :param permission: Enum value from PermissionType indicating the permission to check
    :param trigger: Optional trigger point from PermissionTrigger (e.g., on_load, on_modify)
    :param get_resource_id: Optional function that extracts the resource ID from the context
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            controller = PermissionController.session
            resource_id = get_resource_id(*args, **kwargs) if get_resource_id else None

            if resource_id:
                has_perm = controller.does_user_have_permission(
                    resource_id, permission.value
                )
            else:
                has_perm = controller.user_has_permission(permission.value)

            if not has_perm:
                raise AccessDenied(
                    f"Missing permission '{permission.name}' to execute {func.__name__}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


class restricted_property:
    """
    Property that raises AccessDenied if the user lacks the required permission.
    """
    def __init__(
        self,
        permission: Union[PermissionType, str],
        get_resource_id: Optional[Callable[[Any], str]] = None,
        fallback: Optional[Callable[[Any], Any]] = None,
    ):
        self.permission = permission
        self.get_resource_id = get_resource_id
        self.fallback = fallback

    def __call__(self, func):
        @property
        @wraps(func)
        def wrapper(instance):
            controller = PermissionController.session
            resource_id = (
                self.get_resource_id(instance) if self.get_resource_id else None
            )

            if resource_id:
                allowed = controller.does_user_have_permission(
                    resource_id, self.permission.value if isinstance(self.permission, PermissionType) else self.permission
                )
            else:
                allowed = controller.user_has_permission(
                    self.permission.value if isinstance(self.permission, PermissionType) else self.permission
                )

            if not allowed:
                raise AccessDenied(
                    f"Access denied to restricted property '{func.__name__}'"
                )

            return func(instance)

        return wrapper


class masked_property:
    """
    Property that returns a fallback value if the user lacks the required permission.
    """
    def __init__(
        self,
        permission: Union[PermissionType, str],
        get_resource_id: Optional[Callable[[Any], str]] = None,
        mask: Any = None,
    ):
        self.permission = permission
        self.get_resource_id = get_resource_id
        self.mask = mask

    def __call__(self, func):
        @property
        @wraps(func)
        def wrapper(instance):
            controller = PermissionController.session
            resource_id = (
                self.get_resource_id(instance) if self.get_resource_id else None
            )

            if resource_id:
                allowed = controller.does_user_have_permission(
                    resource_id, self.permission.value if isinstance(self.permission, PermissionType) else self.permission
                )
            else:
                allowed = controller.user_has_permission(
                    self.permission.value if isinstance(self.permission, PermissionType) else self.permission
                )

            if not allowed:
                return self.mask

            return func(instance)

        return wrapper
