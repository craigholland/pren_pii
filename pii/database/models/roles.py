"""
Role hierarchy for Party entities.

A Party (Person or Organization) may have multiple PartyRole records.
Roles are polymorphic and support extension by subclassing.

Abstract roles (PartyRole, PersonRole, OrganizationRole) do not map to domain dataclasses.
Concrete roles (e.g., SystemRole) must subclass from these and inherit ServiceObjectDC.
"""

from typing import Optional
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pii.database.models.core.main import db
from pii.database.models.core.service_object import ServiceObject, ServiceObjectDC

from pii.domain.base.dataclasses import SystemRole as SystemRoleDC


# ---------------------------------------------------------------------------
# PartyRole (abstract base)
# ---------------------------------------------------------------------------

class PartyRole(ServiceObject, db.Model):
    __tablename__ = "party_role"

    # Polymorphic discriminator
    type: Mapped[str] = mapped_column(String(100), index=True)

    # Owning Party
    party_id: Mapped[str] = mapped_column(
        ForeignKey("party.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    party = relationship(
        "Party",
        back_populates="party_roles",
        lazy="joined",
    )

    # Lifecycle
    terminated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )

    # Contact mechanisms that hang off a role (optional; table TBD)
    # contact_mechanisms = relationship(
    #     "ContactMechanism", back_populates="party_role"
    # )

    @declared_attr
    def __mapper_args__(cls):
        if cls.__name__ == "PartyRole":
            return {
                "polymorphic_identity": cls.__name__,
                "polymorphic_on": "type",
            }
        else:
            return {"polymorphic_identity": cls.__name__}

    def __str__(self):
        return self.__class__.__name__

    def is_active(self) -> bool:
        return not self.terminated



# ---------------------------------------------------------------------------
# OrganizationRole (abstract subclass)
# ---------------------------------------------------------------------------

class OrganizationRole(PartyRole):
    __mapper_args__ = {
        "polymorphic_identity": "organization_role",
    }

    person_roles = relationship(
        "PersonRole",
        secondary="person_role_to_organization_role",
        primaryjoin="OrganizationRole.id == person_role_to_organization_role.c.organization_role_id",
        secondaryjoin="PersonRole.id == person_role_to_organization_role.c.person_role_id",
        lazy="selectin",
    )

    managed_person_roles = relationship(
        "OrganizationManagedPersonAssociation",
        back_populates="organization_role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    organization_owner_associations = relationship(
        "OrganizationOwnerAssociation",
        back_populates="organization_role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ---------------------------------------------------------------------------
# PersonRole (abstract subclass)
# ---------------------------------------------------------------------------

class PersonRole(PartyRole):
    is_staff_role: bool = False  # May be toggled in concrete subclasses

    __mapper_args__ = {
        "polymorphic_identity": "person_role",
    }

    organization_roles = relationship(
        "OrganizationRole",
        secondary="person_role_to_organization_role",
        primaryjoin="PersonRole.id == person_role_to_organization_role.c.person_role_id",
        secondaryjoin="OrganizationRole.id == person_role_to_organization_role.c.organization_role_id",
        lazy="selectin",
    )

    organization_owner_associations = relationship(
        "OrganizationOwnerAssociation",
        back_populates="person_role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    organization_managed_person_associations = relationship(
        "OrganizationManagedPersonAssociation",
        back_populates="person_role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    organizations_assigned_to = relationship(
        "OrganizationStaffAssociation",
        back_populates="staff_member",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def is_primary_role(self) -> bool:
        return False

    def can_own_organizations(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# Concrete Role Example
# ---------------------------------------------------------------------------

class SystemRole(PersonRole, ServiceObjectDC):
    __dataclass__ = SystemRoleDC
    __mapper_args__ = {
        "polymorphic_identity": "system_role",
    }


# ---------------------------------------------------------------------------
# Association Models
# ---------------------------------------------------------------------------

class PersonRoleToOrganizationRole(db.Model):
    """Pure link table between PersonRole and OrganizationRole."""

    __tablename__ = "person_role_to_organization_role"

    person_role_id: Mapped[str] = mapped_column(
        ForeignKey("party_role.id"), primary_key=True
    )
    organization_role_id: Mapped[str] = mapped_column(
        ForeignKey("party_role.id"), primary_key=True
    )


class OrganizationManagedPersonAssociation(ServiceObject, db.Model):
    """OrgRole manages a PersonRole (e.g., patient under clinic, user under tenant)."""

    __tablename__ = "organization_managed_person_association"

    organization_role_id: Mapped[str] = mapped_column(
        ForeignKey("party_role.id"), nullable=False, index=True
    )
    person_role_id: Mapped[str] = mapped_column(
        ForeignKey("party_role.id"), nullable=False, index=True
    )

    organization_role = relationship(
        "OrganizationRole",
        back_populates="managed_person_roles",
        foreign_keys=[organization_role_id],
    )
    person_role = relationship(
        "PersonRole",
        back_populates="organization_managed_person_associations",
        foreign_keys=[person_role_id],
    )

    __table_args__ = (
        UniqueConstraint("organization_role_id", "person_role_id", name="uix_managed_person_organization"),
    )


class OrganizationOwnerAssociation(ServiceObject, db.Model):
    """Indicates a PersonRole owns the OrganizationRole's organization."""

    __tablename__ = "organization_owner_association"

    organization_role_id: Mapped[str] = mapped_column(
        ForeignKey("party_role.id"), nullable=False, index=True
    )
    person_role_id: Mapped[str] = mapped_column(
        ForeignKey("party_role.id"), nullable=False, index=True
    )

    organization_role = relationship(
        "OrganizationRole",
        back_populates="organization_owner_associations",
        foreign_keys=[organization_role_id],
    )
    person_role = relationship(
        "PersonRole",
        back_populates="organization_owner_associations",
        foreign_keys=[person_role_id],
    )

    __table_args__ = (
        UniqueConstraint("organization_role_id", "person_role_id", name="uix_owner_organization"),
    )
