from bariendo.common.abstracts.base_store_nodb import BaseStore_NoDB
from bariendo.domain.food.dataclasses import (
    Ingredient,
    Nutrient,
    FoodNutrientSource,
    FoodNutrientDerivation,
    FoodNutrient,
    LabelNutrients,
    Food,
)

class FoodStore_NoDB(BaseStore_NoDB):
    """
    In-memory store for Food entities.
    """
    _dc_model = Food

class IngredientStore_NoDB(BaseStore_NoDB):
    """
    In-memory store for Ingredient entities.
    """
    _dc_model = Ingredient


class NutrientStore_NoDB(BaseStore_NoDB):
    """
    In-memory store for Nutrient entities.
    """
    _dc_model = Nutrient


class FoodNutrientSourceStore_NoDB(BaseStore_NoDB):
    """
    In-memory store for FoodNutrientSource entities.
    """
    _dc_model = FoodNutrientSource


class FoodNutrientDerivationStore_NoDB(BaseStore_NoDB):
    """
    In-memory store for FoodNutrientDerivation entities.
    """
    _dc_model = FoodNutrientDerivation


class FoodNutrientStore_NoDB(BaseStore_NoDB):
    """
    In-memory store for FoodNutrient entities.
    """
    _dc_model = FoodNutrient


class LabelNutrientsStore_NoDB(BaseStore_NoDB):
    """
    In-memory store for LabelNutrients entities.
    """
    _dc_model = LabelNutrients

