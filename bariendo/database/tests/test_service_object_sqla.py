import pytest
from uuid import uuid4
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy import Column, String, Integer
from bariendo.database.models.core.main import db
from bariendo.database.models.core.service_object import ServiceObject, ServiceObjectDC
from bariendo.common.abstracts.base_dataclass import BaseDataclass

# --- Dataclass and ORM Models ---
@dataclass
class SampleDC(BaseDataclass):
    id: str
    name: str
    count: int

class SampleModel(ServiceObjectDC, db.Model):
    __tablename__ = "sample_model_sqla"
    __dataclass__ = SampleDC

    name = Column(String, nullable=False)
    count = Column(Integer, nullable=False)

class AssocOnlyModel(ServiceObject, db.Model):
    __tablename__ = "assoc_model_sqla"

    label = Column(String, nullable=False)


def test_serviceobject_columns(session):
    assoc = AssocOnlyModel(label="assoc test")
    session.add(assoc)
    session.commit()

    assert isinstance(assoc.id, uuid4().__class__)
    assert isinstance(assoc.date_created, datetime)
    assert isinstance(assoc.last_updated, datetime)
    assert assoc.label == "assoc test"
    assert assoc.data_origin is None
    assert assoc._metadata is None

def test_serviceobjectdc_to_dataclass(session):
    uid = str(uuid4())
    instance = SampleModel(id=uid, name="foo", count=5)
    session.add(instance)
    session.commit()

    # Refetch from DB
    obj = session.query(SampleModel).filter_by(id=uid).one()
    dc = obj.to_dataclass()

    assert isinstance(dc, SampleDC)
    assert dc.id == str(uid)
    assert dc.name == "foo"
    assert dc.count == 5

def test_serviceobjectdc_registry():
    assert SampleDC in ServiceObjectDC._dc_to_orm_registry
    assert SampleModel in ServiceObjectDC._orm_to_dc_registry
    assert ServiceObjectDC._dc_to_orm_registry[SampleDC] is SampleModel
    assert ServiceObjectDC._orm_to_dc_registry[SampleModel] is SampleDC
