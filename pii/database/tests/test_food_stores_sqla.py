import pytest
from uuid import UUID

from bariendo.domain.food.dataclasses import (
    Food, Ingredient, Nutrient,
    FoodNutrientSource, FoodNutrientDerivation,
    FoodNutrient, LabelNutrients,
)
from bariendo.database.stores.food import (
    FoodStore, IngredientStore, NutrientStore,
    FoodNutrientSourceStore, FoodNutrientDerivationStore,
    FoodNutrientStore, LabelNutrientsStore,
)


def test_put_get_scan_food_store_sqla():
    store = FoodStore()
    f1 = Food(remote_id=1, description="Apple")
    f2 = Food(remote_id=2, description="Banana")
    s1 = store.put(f1)
    s2 = store.put(f2)

    assert isinstance(s1.id, str) and UUID(s1.id)
    assert isinstance(s2.id, str) and UUID(s2.id)

    got = store.get(s1.id)
    assert isinstance(got, Food)
    assert got.id == s1.id

    all_foods = store.scan()
    assert [f.remote_id for f in all_foods] == [1, 2]


def test_filter_food_store_sqla():
    store = FoodStore()
    store.put(Food(remote_id=10, description="Granola"))
    store.put(Food(remote_id=20, description="Granola Bar"))
    store.put(Food(remote_id=30, description="Muesli"))

    ge20 = store.filter(remote_id__gte=20)
    assert {f.remote_id for f in ge20} == {20, 30}

    gran = store.filter(description__contains="Granola")
    assert {f.remote_id for f in gran} == {10, 20}


def test_delete_food_store_sqla():
    store = FoodStore()
    f = store.put(Food(remote_id=99, description="Toast"))
    assert store.get(f.id) is not None
    store.delete(f.id)
    assert store.get(f.id) is None
    assert store.scan() == []


@pytest.mark.parametrize("Model,Store,extra_kwargs", [
    (Ingredient, IngredientStore, dict(name="X", is_organic=True)),
    (Nutrient, NutrientStore, dict(remote_id=5, number="005", name="Nut", rank=1, unitname="g")),
    (FoodNutrientSource, FoodNutrientSourceStore, dict(remote_id=9, code="SRC", description="Desc")),
    (FoodNutrientDerivation, FoodNutrientDerivationStore,
        lambda: dict(code="DRV", description="Desc", source=FoodNutrientSource(remote_id=101, code="SRCX", description="SDesc"))),
    (FoodNutrient, FoodNutrientStore,
        lambda: dict(remote_id=100,
                     nutrient=Nutrient(remote_id=55, number="055", name="Carb", rank=2, unitname="g"),
                     amount=2.5,
                     derivation=FoodNutrientDerivation(code="DRV", description="Desc",
                                                       source=FoodNutrientSource(remote_id=88, code="SRC88", description="SRCD")))),
    (LabelNutrients, LabelNutrientsStore,
        {fld: 0.0 for fld in (
            'fat','saturated_fat','trans_fat','cholesterol','sodium',
            'carbohydrates','fiber','sugars','protein','calcium','iron','calories'
        )}),
])
def test_other_sqla_stores_basic_crud(Model, Store, extra_kwargs):
    store = Store()
    kwargs = extra_kwargs() if callable(extra_kwargs) else extra_kwargs.copy()
    inst = Model(**kwargs)

    stored = store.put(inst)
    assert isinstance(stored, Model)
    assert isinstance(stored.id, str) and UUID(stored.id)

    got = store.get(stored.id)
    assert got.id == stored.id

    all_objs = store.scan()
    assert any(o.id == stored.id for o in all_objs)

    store.delete(stored.id)
    assert store.get(stored.id) is None
