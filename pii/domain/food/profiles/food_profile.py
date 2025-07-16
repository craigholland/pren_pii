from datetime import datetime, date
from typing import Optional

from bariendo.common.abstracts.base_profile import BaseProfile
from bariendo.common.utils.strings import camel_to_snake
from bariendo.domain.food.dataclasses import (
    Food, Ingredient, Nutrient, FoodNutrient, LabelNutrients, FoodNutrientDerivation, FoodNutrientSource
)
from bariendo.domain.food.stores import FoodStore_NoDB, NutrientStore_NoDB, FoodNutrientSourceStore_NoDB

class FoodProfile(BaseProfile[Food]):
    _store = FoodStore_NoDB
    field_mapping = {"fdcId": "remote_id"}
    external_pk_field = "fdcId"
    @classmethod
    def create(cls, record: dict, deep: bool = False) -> "FoodProfile":
        pass

    @classmethod
    def import_record(cls, record: dict, deep: bool = False) -> Food:
        pass



