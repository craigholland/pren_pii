import pytest
from uuid import uuid4

from pii.domain.base.dataclasses import Person, Organization


# ── Negative type-validation tests ─────────────────────────────────────────

def test_person_invalid_name_type():
    """Person.name must be a str; passing int should fail."""
    with pytest.raises(TypeError):
        Person(id=uuid4(), name=123)

def test_person_invalid_date_of_birth_type():
    """Person.date_of_birth must be a str (ISO8601) or None; passing int fails."""
    with pytest.raises(TypeError):
        Person(id=uuid4(), name="Alice", date_of_birth=20250722)

def test_organization_invalid_legal_name_type():
    """Organization.legal_name must be a str; passing int fails."""
    with pytest.raises(TypeError):
        Organization(name="Org", legal_name=456)

def test_organization_invalid_registration_number_type():
    """Organization.registration_number must be a str or None; passing int fails."""
    with pytest.raises(TypeError):
        Organization(name="Org", legal_name="Legal", registration_number=789)


# ── Resolved relationship-fields tests ─────────────────────────────────────

def test_person_relationship_fields_resolved():
    """
    Person.relationship_fields() should return the actual Organization class
    for its staff_organizations field.
    """
    rels = Person.relationship_fields()
    assert "staff_organizations" in rels
    cls = rels["staff_organizations"]
    assert cls is Organization

def test_organization_relationship_fields_resolved():
    """
    Organization.relationship_fields() should return the actual Organization
    and Person classes for its relationship fields.
    """
    rels = Organization.relationship_fields()

    # parent_links and children_links point to Organization
    for field in ("parent_links", "children_links"):
        assert field in rels
        assert rels[field] is Organization

    # staff_members points to Person
    assert "staff_members" in rels
    assert rels["staff_members"] is Person
