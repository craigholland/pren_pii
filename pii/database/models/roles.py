"""
Regenerated role models using a standalone Table for M:M associations
and proper association_proxy for many-to-many semantics.
"""
from typing import Optional, TYPE_CHECKING
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    Table,
    Column
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.dialects.postgresql import UUID
from pii.database.models.core.main import db
from pii.database.models.core.service_object import ServiceObject, ServiceObjectDC

from pii.domain.base.dataclasses import (
    SystemRole as SystemRoleDC,
    PartyRole as PartyRoleDC,
    PersonRole as PersonRoleDC,
    OrganizationRole as OrganizationRoleDC,
)

if TYPE_CHECKING:
    from pii.database.models.roles import PersonRole, OrganizationRole

# ---------------------------------------------------------------------------
# PartyRole (abstract base)
# ---------------------------------------------------------------------------
class PartyRole(ServiceObjectDC, db.Model):
    __tablename__ = "party_role"
    __dataclass__ = PartyRoleDC

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
# Standalone association table for PersonRole <-> OrganizationRole (M:M)
# Defined after PartyRole to ensure party_role table exists
# ---------------------------------------------------------------------------
person_role_to_organization_role = Table(
    "person_role_to_organization_role",
    ServiceObject.metadata,
    Column(
        "person_role_id", UUID,
        ForeignKey("party_role.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "organization_role_id", UUID,
        ForeignKey("party_role.id", ondelete="CASCADE"),
        primary_key=True
    ),
)

# ---------------------------------------------------------------------------
# OrganizationManagedPersonAssociation (1:M)
# ---------------------------------------------------------------------------
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
        UniqueConstraint(
            "organization_role_id", "person_role_id",
            name="uix_managed_person_organization"
        ),
    )

# ---------------------------------------------------------------------------
# OrganizationOwnerAssociation (1:M)
# ---------------------------------------------------------------------------
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
        UniqueConstraint(
            "organization_role_id", "person_role_id",
            name="uix_owner_organization"
        ),
    )

# ---------------------------------------------------------------------------
# OrganizationRole (abstract subclass)
# ---------------------------------------------------------------------------
class OrganizationRole(PartyRole):
    __mapper_args__ = {
        "polymorphic_identity": "organization_role",
    }
    __dataclass__ = OrganizationRoleDC

    # M:M PersonRole <-> OrganizationRole via standalone Table
    person_roles = relationship(
        "PersonRole",
        secondary=person_role_to_organization_role,
        primaryjoin=lambda: OrganizationRole.id == person_role_to_organization_role.c.organization_role_id,
        secondaryjoin=lambda: PersonRole.id == person_role_to_organization_role.c.person_role_id,
        back_populates="organization_roles",
        lazy="selectin",
    )

    managed_person_roles = relationship(
        "OrganizationManagedPersonAssociation",
        back_populates="organization_role",
        foreign_keys=[OrganizationManagedPersonAssociation.organization_role_id],
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    organization_owner_associations = relationship(
        "OrganizationOwnerAssociation",
        back_populates="organization_role",
        foreign_keys=[OrganizationOwnerAssociation.organization_role_id],
        cascade="all, delete-orphan",
        lazy="selectin",
    )

# ---------------------------------------------------------------------------
# PersonRole (abstract subclass)
# ---------------------------------------------------------------------------
class PersonRole(PartyRole):
    __dataclass__ = PersonRoleDC
    __mapper_args__ = {
        "polymorphic_identity": "person_role",
    }

    is_staff_role: bool = False

    # M:M OrganizationRole <-> PersonRole via standalone Table
    organization_roles = relationship(
        "OrganizationRole",
        secondary=person_role_to_organization_role,
        primaryjoin=lambda: PersonRole.id == person_role_to_organization_role.c.person_role_id,
        secondaryjoin=lambda: OrganizationRole.id == person_role_to_organization_role.c.organization_role_id,
        back_populates="person_roles",
        lazy="selectin",
    )

    organization_managed_person_associations = relationship(
        "OrganizationManagedPersonAssociation",
        back_populates="person_role",
        foreign_keys=[OrganizationManagedPersonAssociation.person_role_id],
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    organization_owner_associations = relationship(
        "OrganizationOwnerAssociation",
        back_populates="person_role",
        foreign_keys=[OrganizationOwnerAssociation.person_role_id],
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
class SystemRole(PersonRole):
    __dataclass__ = SystemRoleDC
    __mapper_args__ = {
        "polymorphic_identity": "system_role",
    }
