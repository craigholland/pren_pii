from dataclasses import dataclass, field
from typing import Optional

from pii.common.abstracts.base_dataclass import BaseDataclass, RelationshipList
from pii.common.utils.uuid_str import UUIDStr

# -----------------------------------------
# Party & Inheritors
# -----------------------------------------

@dataclass
class Party(BaseDataclass):
    """Abstract root for both Person and Organization entities."""
    id: Optional[UUIDStr] = None
    type: str = "party"
    name: str = ""
    notes: Optional[str] = None


@dataclass
class Person(Party):
    """Represents an individual person. Inherits from Party."""
    type: str = "person"
    date_of_birth: Optional[str] = None  # ISO8601-formatted date string
    staff_organizations: RelationshipList["OrganizationStaffAssociationDC"] = field(default_factory=RelationshipList)
    _names_history: RelationshipList["PersonNameDC"] = field(default_factory=RelationshipList)
    _gender_history: RelationshipList["PersonGenderDC"] = field(default_factory=RelationshipList)
    _marital_status_history: RelationshipList["MaritalStatusDC"] = field(default_factory=RelationshipList)


@dataclass
class Organization(Party):
    """Represents an organization or legal entity. Inherits from Party."""
    type: str = "organization"
    legal_name: str = ""
    registration_number: Optional[str] = None
    org_type: Optional[str] = None
    parent_links: RelationshipList["OrganizationToParentOrganizationDC"] = field(default_factory=RelationshipList)
    children_links: RelationshipList["OrganizationToParentOrganizationDC"] = field(default_factory=RelationshipList)
    staff_members: RelationshipList["OrganizationStaffAssociationDC"] = field(default_factory=RelationshipList)


# -----------------------------------------
# Roles
# -----------------------------------------

@dataclass
class PartyRole(BaseDataclass):
    """Base class for roles tied to a Party entity."""
    id: Optional[UUIDStr] = None
    name: str = ""
    description: Optional[str] = None
    party_id: Optional[UUIDStr] = None


@dataclass
class PersonRole(PartyRole):
    """Role associated with a Person (e.g., Employee, Doctor)."""
    pass


@dataclass
class OrganizationRole(PartyRole):
    """Role associated with an Organization (e.g., Hospital, Vendor)."""
    pass


@dataclass
class SystemRole(PartyRole):
    """Globally defined roles used for RBAC (e.g., Admin, System)."""
    pass
