from dataclasses import dataclass, field
from typing import Optional
from datetime import date
from pii.common.abstracts.base_dataclass import BaseDataclass, RelationshipList
from pii.common.utils.uuid_str import UUIDStr
from pii.domain.base.history import (
    PersonName,
    PersonGender,
    MaritalStatus
)
# -----------------------------------------
# Party & Inheritors
# -----------------------------------------

@dataclass(eq=False)
class Party(BaseDataclass):
    """Abstract root for both Person and Organization entities."""
    id: Optional[UUIDStr] = None
    type: str = "party"
    name: str = ""
    notes: Optional[str] = None


@dataclass(eq=False)
class Person(Party):
    """Represents an individual person. Inherits from Party."""
    type: str = "person"
    date_of_birth: Optional[date] = None
    staff_organizations: RelationshipList["Organization"] = field(default_factory=RelationshipList)
    _names_history: RelationshipList[PersonName] = field(default_factory=RelationshipList)
    _gender_history: RelationshipList[PersonGender] = field(default_factory=RelationshipList)
    _marital_status_history: RelationshipList[MaritalStatus] = field(default_factory=RelationshipList)


@dataclass(eq=False)
class Organization(Party):
    """Represents an organization or legal entity. Inherits from Party."""
    type: str = "organization"
    legal_name: str = ""
    registration_number: Optional[str] = None
    org_type: Optional[str] = None
    parent_links: RelationshipList["Organization"] = field(default_factory=RelationshipList)
    children_links: RelationshipList["Organization"] = field(default_factory=RelationshipList)
    staff_members: RelationshipList[Person] = field(default_factory=RelationshipList)


# -----------------------------------------
# Roles
# -----------------------------------------

@dataclass(eq=False)
class PartyRole(BaseDataclass):
    """Base class for roles tied to a Party entity."""
    id: Optional[UUIDStr] = None
    name: str = ""
    description: Optional[str] = None
    party_id: Optional[UUIDStr] = None


@dataclass(eq=False)
class PersonRole(PartyRole):
    """Role associated with a Person (e.g., Employee, Doctor)."""
    pass


@dataclass(eq=False)
class OrganizationRole(PartyRole):
    """Role associated with an Organization (e.g., Hospital, Vendor)."""
    pass


@dataclass(eq=False)
class SystemRole(PartyRole):
    """Globally defined roles used for RBAC (e.g., Admin, System)."""
    pass
