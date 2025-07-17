import json
import pytest
from pathlib import Path

from pii.domain.food.dataclasses import Food, Nutrient
from pii.domain.food.profiles.food_profile import FoodProfile
from pii.domain.food.profiles.nutrient_profile import NutrientProfile

from pii.database.stores.food import (
    FoodStore,
    NutrientStore,
)

# Load shared test data from file
TEST_DATA_PATH = Path(__file__).parent.parent.parent.parent / "tests" / "test_data.json"
RAW_DATA = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))

@pytest.fixture
def sample_food_dict():
    return RAW_DATA[0]

@pytest.fixture
def sample_nutrient_dict():
    return RAW_DATA[0]["foodNutrients"][0]["nutrient"]

def test_food_profile_create_and_save_sqla(sample_food_dict):
    FoodProfile._store = FoodStore
    profile = FoodProfile.create(sample_food_dict, deep=True)
      # manually inject DB store
    profile.save()
    food = profile.get()
    assert isinstance(food, Food)
    assert food.remote_id == sample_food_dict["fdcId"]

def test_food_profile_import_record_deep_sqla(sample_food_dict):
    FoodProfile._store = FoodStore
    food = FoodProfile.import_record(sample_food_dict, deep=True)
    assert isinstance(food, Food)
    assert food.description == sample_food_dict["description"]
    assert str(food.remote_id) == str(sample_food_dict["fdcId"])
    assert len(food.nutrients) > 0
    assert any(n.nutrient.name == "Protein" for n in food.nutrients)

def test_nutrient_profile_create_and_save_sqla(sample_nutrient_dict):
    profile = NutrientProfile.create(sample_nutrient_dict)
    profile._store = NutrientStore  # manually inject DB store
    profile.save()
    nutrient = profile.get()
    assert isinstance(nutrient, Nutrient)
    assert nutrient.remote_id == sample_nutrient_dict["id"]
    assert nutrient.name == sample_nutrient_dict["name"]

def test_nutrient_profile_import_record_shallow_sqla(sample_nutrient_dict):
    NutrientProfile._store = NutrientStore
    nutrient = NutrientProfile.import_record(sample_nutrient_dict, deep=False)
    assert isinstance(nutrient, Nutrient)
    assert nutrient.name == sample_nutrient_dict["name"]
