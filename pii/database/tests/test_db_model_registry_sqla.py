import pytest
from dataclasses import is_dataclass, dataclass
from bariendo.database.models.core.service_object import ServiceObjectDC
from bariendo.database.store_adapters.sqlalchemy_store import BaseStoreSQLAlchemy


def test_serviceobjectdc_registries_are_inverse():
    dc_to_orm = ServiceObjectDC._dc_to_orm_registry
    orm_to_dc = ServiceObjectDC._orm_to_dc_registry

    # we should have at least one mapping:
    assert dc_to_orm, "No dataclass→ORM mappings registered"
    assert orm_to_dc, "No ORM→dataclass mappings registered"

    # and they should be true inverses:
    for dc, orm in dc_to_orm.items():
        assert is_dataclass(dc), f"{dc!r} is not a dataclass"
        assert issubclass(orm, ServiceObjectDC), f"{orm!r} is not an ORM-model"
        assert orm_to_dc.get(orm) is dc, f"Inverse mapping broken for {dc} ↔ {orm}"


def test_every_model_has_a_store_registered():
    BaseStoreSQLAlchemy._auto_discover_stores()

    dc_to_orm = ServiceObjectDC._dc_to_orm_registry
    model_to_store = BaseStoreSQLAlchemy._model_to_store_registry

    for dc, orm in dc_to_orm.items():
        assert orm in model_to_store, f"No store registered for ORM model {orm!r}"


@pytest.mark.parametrize("dc,orm", list(ServiceObjectDC._dc_to_orm_registry.items()))
def test_get_store_for_dataclass_class(dc, orm):
    store = BaseStoreSQLAlchemy.get_store_for(dc)
    store_cls = BaseStoreSQLAlchemy._model_to_store_registry[orm]

    # we get back an instance of the right Store class
    assert isinstance(store, store_cls)
    # and that store still points at the correct ORM model
    assert getattr(store, "_model") is orm


@pytest.mark.parametrize("orm,dc", list(ServiceObjectDC._orm_to_dc_registry.items()))
def test_get_store_for_orm_model_class(orm, dc):
    store = BaseStoreSQLAlchemy.get_store_for(orm)
    store_cls = BaseStoreSQLAlchemy._model_to_store_registry[orm]

    assert isinstance(store, store_cls)
    assert getattr(store, "_model") is orm


def test_get_store_for_bad_inputs():
    # totally unrecognized type
    with pytest.raises(TypeError):
        BaseStoreSQLAlchemy.get_store_for(123)

    # a dataclass we never registered
    @dataclass
    class FooDC:
        x: int

    with pytest.raises(LookupError):
        BaseStoreSQLAlchemy.get_store_for(FooDC)

    # an ORM-model subclass we never registered
    class DummyModel(ServiceObjectDC):
        __abstract__ = True
        __dataclass__ = FooDC

    with pytest.raises(LookupError):
        BaseStoreSQLAlchemy.get_store_for(DummyModel)
