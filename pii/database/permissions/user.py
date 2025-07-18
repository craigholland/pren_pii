from dataclasses import dataclass, field
from typing import List, Set, Optional
from pii.common.abstracts.base_dataclass import BaseDataclass

@dataclass
class UserRole(BaseDataclass):
    id: Optional[str] = None
    name: str = ""

@dataclass
class UserPermissionInfo(BaseDataclass):
    user_id: Optional[str] = None
    roles: List[UserRole] = field(default_factory=list)
    permissions: Set[str] = field(default_factory=set)
