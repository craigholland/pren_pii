from typing import Literal, Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.hybrid import hybrid_property

from pii.database.models.history import History
from pii.database.models.core.main import db
from pii.database.models.core.service_object import ServiceObject, ServiceObjectDC
from pii.database.models.core.validators.person import PersonValidator

from pii.domain.enums import PersonNameType
from pii.domain.base.dataclasses import (
    Party as PartyDC,
    Person as PersonDC,
    Organization as OrganizationDC,
)

# -----------------------------------------------------------------------------
# Base Party Model (with dataclass)
# -----------------------------------------------------------------------------

class Party(ServiceObjectDC, db.Model):
    __tablename__ = "party"
    __dataclass__ = PartyDC

    type: Mapped[Literal["party", "person", "organization"]] = mapped_column(
        String(50), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "party",
        "with_polymorphic": "*",
    }

    party_roles: Mapped[list["PartyRole"]] = relationship(
        "PartyRole",
        back_populates="party",
        cascade="all, delete-orphan"
    )


# -----------------------------------------------------------------------------
# Person (inherits Party, has dataclass)
# -----------------------------------------------------------------------------

class Person(Party):
    __tablename__ = "person"
    __dataclass__ = PersonDC
    __validator__ = PersonValidator

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("party.id"), primary_key=True
    )
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "person",
    }

    # Relationships
    staff_organizations: Mapped[list["OrganizationStaffAssociation"]] = relationship(
        "OrganizationStaffAssociation",
        back_populates="staff_person",
        cascade="all, delete-orphan"
    )

    _names_history = relationship(
        "PersonName", back_populates="person", cascade="all, delete-orphan"
    )
    _gender_history = relationship(
        "PersonGender", back_populates="person", cascade="all, delete-orphan"
    )
    _marital_status_history = relationship(
        "MaritalStatus", back_populates="person", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Person | {self.full_name}, {self.id}>"

    @hybrid_property
    def gender(self):
        return History.current(self._gender_history)

    @hybrid_property
    def marital_status(self):
        return History.current(self._marital_status_history)

    @hybrid_property
    def first_name(self):
        return History.current(self._names_history, PersonNameType.FIRST)

    @hybrid_property
    def last_name(self):
        return History.current(self._names_history, PersonNameType.LAST)

    @property
    def full_name(self):
        return " ".join(p for p in [self.first_name, self.last_name] if p)


# -----------------------------------------------------------------------------
# Organization (inherits Party, has dataclass)
# -----------------------------------------------------------------------------

class Organization(Party):
    __tablename__ = "organization"
    __dataclass__ = OrganizationDC

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("party.id"), primary_key=True
    )
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    org_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "organization",
    }

    parent_links: Mapped[list["OrganizationToParentOrganization"]] = relationship(
        "OrganizationToParentOrganization",
        back_populates="child_org",
        foreign_keys="OrganizationToParentOrganization.child_org_id",
        cascade="all, delete-orphan"
    )

    children_links: Mapped[list["OrganizationToParentOrganization"]] = relationship(
        "OrganizationToParentOrganization",
        back_populates="parent_org",
        foreign_keys="OrganizationToParentOrganization.parent_org_id",
        cascade="all, delete-orphan"
    )

    staff_members: Mapped[list["OrganizationStaffAssociation"]] = relationship(
        "OrganizationStaffAssociation",
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Organization | {self.legal_name}, {self.id}>"


# -----------------------------------------------------------------------------
# Association: Org-to-ParentOrg (no dataclass)
# -----------------------------------------------------------------------------

class OrganizationToParentOrganization(ServiceObject, db.Model):
    __tablename__ = "organization_to_parent_org"

    child_org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organization.id"), primary_key=True
    )
    parent_org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organization.id"), primary_key=True
    )

    child_org: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[child_org_id],
        back_populates="parent_links"
    )
    parent_org: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[parent_org_id],
        back_populates="children_links"
    )


# -----------------------------------------------------------------------------
# Association: Org-to-StaffPerson (no dataclass)
# -----------------------------------------------------------------------------

class OrganizationStaffAssociation(ServiceObject, db.Model):
    __tablename__ = "organization_staff_assoc"
    __table_args__ = (
        UniqueConstraint("organization_id", "staff_person_id", name="uq_org_staff"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organization.id"), primary_key=True
    )
    staff_person_id: Mapped[UUID] = mapped_column(
        ForeignKey("person.id"), primary_key=True
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="staff_members"
    )
    staff_person: Mapped["Person"] = relationship(
        "Person", back_populates="staff_organizations"
    )
