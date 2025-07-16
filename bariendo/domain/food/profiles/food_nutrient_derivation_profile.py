from typing import Optional, Union

from bariendo.common.abstracts.base_profile import BaseProfile
from bariendo.domain.food.dataclasses import FoodNutrientDerivation, FoodNutrientSource
from bariendo.domain.food.stores import FoodNutrientSourceStore_NoDB
from bariendo.domain.food.profiles.food_nutrient_source_profile import FoodNutrientSourceProfile


class FoodNutrientDerivationProfile(BaseProfile[FoodNutrientDerivation]):
    _store = FoodNutrientSourceStore_NoDB
    _import_mapping = {}

    @classmethod
    def import_record(cls, record: dict, deep: bool = False) -> FoodNutrientDerivation:
        mapped = cls._apply_import_mapping(record, deep=deep)
        cleaned = cls()._recursive_remap(mapped)

        # Handle nested foodNutrientSource
        source_data = cleaned.get("foodNutrientSource") or {}
        if not isinstance(source_data, FoodNutrientSource):
            source = FoodNutrientSourceProfile.import_record(source_data, deep=deep)
        else:
            source = source_data

        derivation = FoodNutrientDerivation(
            code=cleaned.get("code", ""),
            description=cleaned.get("description"),
            source=source,
        )

        if deep:
            cls._store().put(derivation)

        return derivation

    @classmethod
    def create(cls, record: dict, deep: bool = False) -> "FoodNutrientDerivationProfile":
        deriv = cls.import_record(record, deep=deep)
        profile = cls()
        profile._store.put(deriv)
        profile._instance = deriv
        return profile

    def update(self, obj: Union[dict, FoodNutrientDerivation], deep: bool = False) -> None:
        updated = self.import_record(obj, deep=deep)
        self._instance = updated
        self._store.put(updated)
