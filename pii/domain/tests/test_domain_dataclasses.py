from uuid import uuid4

from pii.common.utils.uuid_str import UUIDStr
from pii.domain.base.dataclasses import (
    Person,
    Organization,
    PersonRole,
    OrganizationRole,
    SystemRole,
)

def test_person_relationship_fields():
    """Person.relationship_fields() should list its RelationshipList attributes."""
    rels = Person.relationship_fields()
    expected = {
        "staff_organizations",
        "_names_history",
        "_gender_history",
        "_marital_status_history",
    }
    assert set(rels) == expected

def test_organization_relationship_fields():
    """Organization.relationship_fields() should list its RelationshipList attributes."""
    rels = Organization.relationship_fields()
    expected = {"parent_links", "children_links", "staff_members"}
    assert set(rels) == expected

def test_person_equality_and_hashing():
    """Two Person instances with the same id should be equal and have the same hash."""
    pid1 = UUIDStr(str(uuid4()))
    pid2 = UUIDStr(str(uuid4()))
    a = Person(id=pid1, name="Alice")
    b = Person(id=pid1, name="Bob")
    assert a == b
    assert hash(a) == hash(b)
    c = Person(id=pid2, name="Alice")
    assert a != c

def test_organization_defaults_and_assignment():
    """Organization defaults 'type' and allows setting name and legal_name."""
    org = Organization(name="Acme", legal_name="Acme Corporation Ltd")
    assert org.type == "organization"
    assert org.name == "Acme"
    assert org.legal_name == "Acme Corporation Ltd"

def test_role_inheritance_and_defaults():
    """PartyRole subclasses should inherit default behavior and allow overrides."""
    for RoleCls in (PersonRole, OrganizationRole, SystemRole):
        r = RoleCls(name="TestRole", description="Desc")
        assert r.id is None
        assert r.name == "TestRole"
        assert r.description == "Desc"
        # party_id should be assignable
        r.party_id = "some-uuid"
        assert r.party_id == "some-uuid"
