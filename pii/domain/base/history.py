from dataclasses import dataclass, field
from typing import Optional

from pii.common.abstracts.base_dataclass import BaseDataclass, RelationshipList
from pii.common.utils.uuid_str import UUIDStr
from pii.domain.enums import PersonNameType, GenderType, MaritalStatusType

@dataclass(eq=False)
class PersonName(BaseDataclass):
    name: str
    name_type: PersonNameType
    person_id: UUIDStr


@dataclass(eq=False)
class PersonGender(BaseDataclass):
    gender: GenderType
    person_id: UUIDStr


@dataclass(eq=False)
class MaritalStatus(BaseDataclass):
    status: MaritalStatusType
    person_id: UUIDStr