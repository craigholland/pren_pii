from dataclasses import dataclass, field
from typing import Optional

from pii.common.abstracts.base_dataclass import BaseDataclass, RelationshipList


# -----------------------------------------
# Party & Inheritors
# -----------------------------------------

@dataclass
class Party(BaseDataclass):
    id: Optional[str] = None
    type: str = "party"
    name: str = ""
    notes: Optional[str] = None


@dataclass
class Person(Party):
    type: str = "person"
    date_of_birth: Optional[str] = None  # ISO8601 string for datetime
    staff_organizations: RelationshipList["OrganizationStaffAssociationDC"] = field(default_factory=RelationshipList)
    _names_history: RelationshipList["PersonNameDC"] = field(default_factory=RelationshipList)
    _gender_history: RelationshipList["PersonGenderDC"] = field(default_factory=RelationshipList)
    _marital_status_history: RelationshipList["MaritalStatusDC"] = field(default_factory=RelationshipList)


@dataclass
class Organization(Party):
    type: str = "organization"
    legal_name: str = ""
    registration_number: Optional[str] = None
    org_type: Optional[str] = None
    parent_links: RelationshipList["OrganizationToParentOrganizationDC"] = field(default_factory=RelationshipList)
    children_links: RelationshipList["OrganizationToParentOrganizationDC"] = field(default_factory=RelationshipList)
    staff_members: RelationshipList["OrganizationStaffAssociationDC"] = field(default_factory=RelationshipList)


# -----------------------------------------
# Roles – Concrete
# -----------------------------------------

@dataclass
class SystemRole(BaseDataclass):
    id: Optional[str] = None
    name: str = ""
    description: Optional[str] = None
    party_id: Optional[str] = None
