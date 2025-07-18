from enum import Enum

class PermissionType(str, Enum):
    CAN_CREATE = "can_create"
    CAN_READ = "can_read"
    CAN_READ_FIELD = "can_read_field"
    CAN_UPDATE = "can_update"
    CAN_UPDATE_FIELD = "can_update_field"
    CAN_DELETE = "can_delete"
    GET_RESOURCE_ID = "get_resource_id"
    HAS_READ_ACCESS = "has_read_access"
    HAS_UPDATE_ACCESS = "has_update_access"
    HAS_DELETE_ACCESS = "has_delete_access"
    HAS_CREATE_ACCESS = "has_create_access"

class PermissionTrigger(str, Enum):
    ON_LOAD = "on_load"
    ON_REFRESH = "on_refresh"
    ON_MODIFY = "on_modify"
    ON_BEFORE_DELETE = "on_before_delete"
