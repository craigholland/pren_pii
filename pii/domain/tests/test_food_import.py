# test_food_profiles.py

import json
from pathlib import Path
import pytest

from pii.domain.food.dataclasses import Food, Nutrient
from pii.domain.food.profiles.food_profile import FoodProfile
from pii.domain.food.profiles.nutrient_profile import NutrientProfile

# Load actual test data
TEST_DATA_PATH = Path(__file__).parent.parent.parent.parent / "tests" / "test_data.json"
TEST_DATA = json.loads(TEST_DATA_PATH.read_text())


@pytest.fixture
def sample_food_dict():
    return TEST_DATA[0]  # Use first food sample for focused tests


@pytest.fixture
def sample_nutrient_dict():
    return TEST_DATA[0]["foodNutrients"][0]["nutrient"]


def test_food_profile_create_and_save(sample_food_dict):
    profile = FoodProfile.create(sample_food_dict, deep=True)
    assert isinstance(profile.get(), Food)
    assert profile.get().remote_id == sample_food_dict["fdcId"]


def test_food_profile_import_record_deep(sample_food_dict):
    food_dc = FoodProfile.import_record(sample_food_dict, deep=True)
    assert food_dc.description == sample_food_dict["description"]
    assert str(food_dc.remote_id) == str(sample_food_dict["fdcId"])
    assert len(food_dc.nutrients) == len(sample_food_dict.get("foodNutrients", []))


def test_food_profile_fallback_remote_id():
    record = {
        "description": "Fallback Food",
        "ingredients": "",
        "foodNutrients": []
    }
    profile = FoodProfile.create(record, deep=False)
    food = profile.get()
    assert food.remote_id is None
    assert food.description == "Fallback Food"


def test_food_profile_import_with_empty_nutrients():
    record = {
        "fdcId": 123,
        "description": "Food with no nutrients",
        "foodNutrients": []
    }
    food = FoodProfile.import_record(record, deep=True)
    assert food.remote_id == 123
    assert food.description == "Food with no nutrients"
    assert food.nutrients == []


def test_label_nutrient_parsing_with_missing_values():
    record = {
        "fdcId": 123,
        "description": "Incomplete Nutrient Data",
        "labelNutrients": {
            "fat": {},
            "sodium": {"value": 0.0},
            "fiber": None
        }
    }
    food = FoodProfile.import_record(record, deep=False)
    assert food.label_nutrients.fat == 0.0
    assert food.label_nutrients.sodium == 0.0
    assert food.label_nutrients.fiber == 0.0


def test_nutrient_profile_create_and_update(sample_nutrient_dict):
    profile = NutrientProfile.create(sample_nutrient_dict, deep=False)
    nutrient = profile.get()
    assert isinstance(nutrient, Nutrient)
    assert nutrient.remote_id == sample_nutrient_dict["id"]
    assert nutrient.name == sample_nutrient_dict["name"]


def test_nutrient_profile_import_record_shallow(sample_nutrient_dict):
    nutrient = NutrientProfile.import_record(sample_nutrient_dict, deep=False)
    assert nutrient.remote_id == sample_nutrient_dict["id"]
    assert nutrient.name == sample_nutrient_dict["name"]


def test_nutrient_profile_import_with_invalid_type():
    with pytest.raises(ValueError):
        NutrientProfile.import_record("not a dict")
