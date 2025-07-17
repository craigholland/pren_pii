import pytest
from uuid import uuid4

from pii.domain.food.dataclasses import (
    Food, Ingredient, Nutrient,
    FoodNutrientSource, FoodNutrientDerivation,
    FoodNutrient, LabelNutrients
)
from pii.domain.food.stores import (
    FoodStore_NoDB, IngredientStore_NoDB, NutrientStore_NoDB,
    FoodNutrientSourceStore_NoDB, FoodNutrientDerivationStore_NoDB,
    FoodNutrientStore_NoDB, LabelNutrientsStore_NoDB
)

def test_food_dataclass_defaults_and_assignment():
    fid = uuid4()
    f = Food(id=fid, remote_id=42, description="Granola Bar")
    # basic fields
    assert f.id == str(fid)
    assert f.remote_id == 42
    assert f.description == "Granola Bar"
    # defaults for optional fields
    assert f.branded_food_category is None
    assert f.ingredients == []
    assert f.nutrients == []
    assert f.label_nutrients is None

def test_label_nutrients_dataclass():
    ln_id = uuid4()
    ln = LabelNutrients(
        id=ln_id, fat=7.0, saturated_fat=2.0, trans_fat=0.0,
        cholesterol=0.0, sodium=45.1, carbohydrates=16.0,
        fiber=1.99, sugars=5.99, protein=3.0,
        calcium=19.9, iron=1.08, calories=140.0
    )
    assert ln.id == str(ln_id)
    # spot check a couple
    assert ln.protein == 3.0
    assert ln.calories == 140.0

def test_put_get_scan_food_store():
    store = FoodStore_NoDB()
    f1 = Food(id=uuid4(), remote_id=1, description="Apple")
    f2 = Food(id=uuid4(), remote_id=2, description="Banana")
    store.put(f1)
    store.put(f2)
    # get by id
    assert store.get(f1.id) is f1
    assert store.get(f2.id) is f2
    # scan returns both (order is insertion order)
    assert store.scan() == [f1, f2]

def test_filter_food_store():
    store = FoodStore_NoDB()
    f1 = Food(id=uuid4(), remote_id=1, description="Apple Pie")
    f2 = Food(id=uuid4(), remote_id=2, description="Banana Split")
    store.put(f1)
    store.put(f2)
    # filter by remote_id >= 2
    res = store.filter(remote_id__gte=2)
    assert res == [f2]
    # filter by description contains "Pie"
    res = store.filter(description__contains="Pie")
    assert res == [f1]
    # no matches
    assert store.filter(description="Nothing") == []

def test_delete_food_store():
    store = FoodStore_NoDB()
    f = Food(id=uuid4(), remote_id=5, description="Toast")
    store.put(f)
    assert store.get(f.id) is f
    store.delete(f.id)
    assert store.get(f.id) is None
    assert store.scan() == []

@pytest.mark.parametrize("Model,Store", [
    (Ingredient, IngredientStore_NoDB),
    (Nutrient, NutrientStore_NoDB),
    (FoodNutrientSource, FoodNutrientSourceStore_NoDB),
    (FoodNutrientDerivation, FoodNutrientDerivationStore_NoDB),
    (FoodNutrient, FoodNutrientStore_NoDB),
    (LabelNutrients, LabelNutrientsStore_NoDB),
])
def test_other_dataclass_stores_basic_crud(Model, Store):
    """Generic smoke-test for all other NoDB stores."""
    store = Store()
    # create an instance with only the required fields
    # most models require an `id` and possibly one other field,
    # so we build minimal valid kwargs
    kwargs = {'id': uuid4()}
    # add extra required args if needed:
    if Model is Ingredient:
        kwargs.update(name="X", is_organic=False)
    elif Model is Nutrient:
        kwargs.update(remote_id=100, number="001", name="Test", rank=1, unitname="g")
    elif Model is FoodNutrientSource:
        kwargs.update(remote_id=10, code="SRC", description="Desc")
    elif Model is FoodNutrientDerivation:
        # need a source instance
        src = FoodNutrientSource(id=uuid4(), remote_id=10, code="SRC", description="Desc")
        kwargs.update(code="DRV", description="Derived", source=src)
    elif Model is FoodNutrient:
        # need nested Nutrient & Derivation
        nutr = Nutrient(id=uuid4(), remote_id=100, number="001", name="N", rank=1, unitname="g")
        drv = FoodNutrientDerivation(
            id=uuid4(), code="DRV", description="Desc", source=FoodNutrientSource(
                id=uuid4(), remote_id=10, code="SRC", description="Desc"))
        kwargs.update(remote_id=999, nutrient=nutr, amount=5.0, derivation=drv)
    elif Model is LabelNutrients:
        # fill all floats with zero
        for fld in ('fat','saturated_fat','trans_fat','cholesterol','sodium',
                    'carbohydrates','fiber','sugars','protein','calcium','iron','calories'):
            kwargs[fld] = 0.0

    inst = Model(**kwargs)
    # CRUD operations
    stored = store.put(inst)
    assert stored is inst
    fetched = store.get(inst.id)
    assert fetched is inst
    all_objs = store.scan()
    assert inst in all_objs
    # cleanup
    store.delete(inst.id)
    assert store.get(inst.id) is None


def test_patch_food_store():
    store = FoodStore_NoDB()
    f = Food(id=uuid4(), remote_id=5, description="Toast")
    store.put(f)

    # Create patch data with only description changed
    patch_data = Food(id=f.id, description="Buttered Toast")
    result = store._patch(patch_data)

    # Verify only description changed, remote_id preserved
    assert result.id == f.id
    assert result.description == "Buttered Toast"
    assert result.remote_id == 5


def test_get_nonexistent_food():
    store = FoodStore_NoDB()
    random_id = uuid4()
    assert store.get(random_id) is None


def test_update_nonexistent_food():
    store = FoodStore_NoDB()
    non_existent = Food(id=uuid4(), description="Doesn't Exist")
    # Should either raise an error or fall back to insert depending on your implementation
    result = store.put(non_existent)
    assert result.id == non_existent.id
    assert store.get(non_existent.id) is not None


def test_filter_food_store():
    store = FoodStore_NoDB()
    store.put(Food(id=uuid4(), remote_id=10, description="Granola"))
    store.put(Food(id=uuid4(), remote_id=20, description="Granola Bar"))
    store.put(Food(id=uuid4(), remote_id=30, description="Muesli"))

    # Test filtering by description containing "Granola"
    results = store.filter(description__contains="Granola")
    assert len(results) == 2
    assert all("Granola" in f.description for f in results)

    # Test filtering by remote_id greater than 15
    results = store.filter(remote_id__gte=15)
    assert len(results) == 2
    assert all(f.remote_id > 15 for f in results)

