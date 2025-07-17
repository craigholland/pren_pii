
import pytest
from pii.domain.food.profiles.food_profile import FoodProfile
from pii.domain.food.profiles.nutrient_profile import NutrientProfile
from pii.domain.food.dataclasses import Food, Nutrient

@pytest.fixture
def sample_food_dict():
    return {
        "fdcId": 1106281,
        "description": "GRANOLA, CINNAMON, RAISIN, CINNAMON, RAISIN",
        "brandedFoodCategory": "Cereal",
        "brandOwner": "MICHELE'S",
        "ingredients": "OATS, RAISINS",
        "publicationDate": "11/13/2020",
        "servingSize": 28,
        "servingSizeUnit": "g",
        "householdServingFullText": "0.25 cup",
        "foodNutrients": [
            {
                "id": 13694818,
                "amount": 10.7,
                "nutrient": {
                    "id": 1003,
                    "number": "203",
                    "name": "Protein",
                    "rank": 600,
                    "unitName": "g"
                },
                "foodNutrientDerivation": {
                    "code": "LCCS",
                    "description": "Calculated from value per serving size measure",
                    "foodNutrientSource": {
                        "id": 9,
                        "code": "12",
                        "description": "Manufacturer's analytical; partial documentation"
                    }
                }
            }
        ],
        "labelNutrients": {
            "fat": {"value": 7.0},
            "saturatedFat": {"value": 2.0},
            "transFat": {"value": 0.0},
            "cholesterol": {"value": 0.0},
            "sodium": {"value": 45.1},
            "carbohydrates": {"value": 16.0},
            "fiber": {"value": 1.99},
            "sugars": {"value": 5.99},
            "protein": {"value": 3.0},
            "calcium": {"value": 19.9},
            "iron": {"value": 1.08},
            "calories": {"value": 140},
        },
    }

@pytest.fixture
def sample_nutrient_dict():
    return {
        "id": 1003,
        "name": "Protein",
        "number": "203",
        "rank": 600,
        "unitName": "g"
    }

def test_food_profile_create_and_save(sample_food_dict):
    profile = FoodProfile.create(sample_food_dict, deep=True)
    assert isinstance(profile, FoodProfile)
    food = profile.get()
    assert isinstance(food, Food)
    assert food.remote_id == sample_food_dict["fdcId"]

def test_food_profile_import_record_deep(sample_food_dict):
    food_dc = FoodProfile.import_record(sample_food_dict, deep=True)
    assert food_dc.description == sample_food_dict["description"]
    assert str(food_dc.remote_id) == str(sample_food_dict["fdcId"])
    assert len(food_dc.nutrients) == 1
    assert food_dc.nutrients[0].nutrient.name == "Protein"

def test_food_profile_import_with_empty_nutrients():
    record = {
        "fdcId": 123456,
        "description": "Empty Nutrients",
        "ingredients": "",
        "foodNutrients": [],
    }
    food = FoodProfile.import_record(record, deep=True)
    assert food.remote_id == 123456
    assert food.nutrients == []

def test_label_nutrient_parsing_with_missing_values():
    record = {
        "fdcId": 55555,
        "description": "Partial Label Nutrients",
        "labelNutrients": {
            "protein": {"value": 5.0},
            "calcium": {"value": 20.0},
        }
    }
    food = FoodProfile.import_record(record)
    assert food.label_nutrients.protein == 5.0
    assert food.label_nutrients.calcium == 20.0
    assert food.label_nutrients.fat == 0.0  # not present in input

def test_nutrient_profile_create_and_update(sample_nutrient_dict):
    profile = NutrientProfile.create(sample_nutrient_dict, deep=False)
    assert isinstance(profile, NutrientProfile)
    nutrient = profile.get()
    assert isinstance(nutrient, Nutrient)
    assert nutrient.remote_id == 1003
    assert nutrient.name == "Protein"

def test_nutrient_profile_import_record_shallow(sample_nutrient_dict):
    nutrient = NutrientProfile.import_record(sample_nutrient_dict, deep=False)
    assert isinstance(nutrient, Nutrient)
    assert nutrient.name == sample_nutrient_dict["name"]

def test_nutrient_profile_import_with_invalid_type():
    with pytest.raises(TypeError):
        NutrientProfile.import_record("not a dict")
