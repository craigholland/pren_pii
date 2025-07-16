import json
from pathlib import Path
import pytest
from uuid import UUID

from bariendo.domain.food.dataclasses import Food
from bariendo.database.stores.food import FoodStore
from bariendo.domain.food.profiles import FoodProfile
from bariendo.domain.food.interfaces import FoodInterface

# point the FoodProfile at the SQLAlchemy store
FoodProfile._store = FoodStore

# same test JSON you were using
TEST_DATA = (
    Path(__file__).parent.parent.parent.parent
    / "tests"
    / "test_data.json"
)

def test_db_import_single_record():
    records = json.loads(TEST_DATA.read_text())
    assert records, "No test records found"
    first = records[0]

    # import via the interface
    iface = FoodInterface.import_(first)
    foods = iface.profile.foods

    # domain object checks
    assert len(foods) == 1
    f = foods[0]
    assert isinstance(f, Food)
    assert isinstance(f.id, str) and UUID(f.id)
    assert f.description == first["description"]
    assert f.remote_id == first["fdcId"]
    assert len(f.nutrients) == len(first["foodNutrients"])
    ln_data = first.get("labelNutrients")
    if ln_data:
        assert f.label_nutrients is not None
        assert f.label_nutrients.calories == ln_data["calories"]["value"]
    else:
        assert f.label_nutrients is None

    # now ensure it's in the DB
    store = FoodStore()
    persisted = store.scan()
    assert len(persisted) == 1
    db_f = persisted[0]
    # matches the one we just imported
    assert db_f.id == f.id
    assert db_f.remote_id == f.remote_id
    assert db_f.description == f.description

def test_db_batch_import_records():
    records = json.loads(TEST_DATA.read_text())
    assert records, "No test records found"

    # import all
    interfaces = FoodInterface.import_many(records)

    # one interface per JSON record
    assert len(interfaces) == len(records)

    # check DB contents
    store = FoodStore()
    all_foods = store.scan()
    assert len(all_foods) == len(records)

    ids = []
    for iface in interfaces:
        foods = iface.profile.foods
        assert len(foods) == 1
        f = foods[0]
        assert isinstance(f, Food)
        assert f.remote_id is not None
        assert f.description
        ids.append(f.id)

    # ensure all IDs unique
    assert len(ids) == len(set(ids))

    # and DB scan IDs match
    db_ids = {f.id for f in all_foods}
    assert set(ids) == db_ids

def test_db_import_persists_ingredients():
    records = json.loads(TEST_DATA.read_text())
    first = records[0]

    iface = FoodInterface.import_(first)
    f = iface.profile.foods[0]

    # reload from DB to avoid memory illusions
    store = FoodStore()
    db_f = store.get(f.id)
    assert db_f.id == f.id

    # ensure ingredients persisted and match
    orig_ingredients = {i.strip().lower() for i in first["ingredients"].split(",") if i.strip()}
    db_ingredients = {i.name.lower() for i in db_f.ingredients}
    assert orig_ingredients == db_ingredients


def test_db_import_persists_nutrients():
    records = json.loads(TEST_DATA.read_text())
    first = records[0]

    iface = FoodInterface.import_(first)
    f = iface.profile.foods[0]

    # reload from DB to verify persistence
    store = FoodStore()
    db_f = store.get(f.id)

    # verify nutrient integrity
    orig_nutrient_ids = {fn["id"] for fn in first["foodNutrients"]}
    db_nutrient_ids = {n.remote_id for n in db_f.nutrients}
    assert orig_nutrient_ids == db_nutrient_ids

    # optional: validate nested derivation + source exist
    for n in db_f.nutrients:
        assert n.derivation is not None
        assert n.derivation.source is not None

def test_db_import_persists_label_nutrients():
    records = json.loads(TEST_DATA.read_text())
    first = records[0]

    iface = FoodInterface.import_(first)
    f = iface.profile.foods[0]

    store = FoodStore()
    db_f = store.get(f.id)

    ln_data = first.get("labelNutrients", {})
    for k, v in ln_data.items():
        if hasattr(db_f.label_nutrients, k):
            assert getattr(db_f.label_nutrients, k) == v["value"]
