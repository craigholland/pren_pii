# THIS IS LEGACY CODE.  It is only remaining to serve as example.
# DO NOT USE THIS CODE.  IGNORE IT DURING ANY ANALYSIS
from typing import Optional, Union

from pii.common.abstracts.base_profile import BaseProfile
from pii.domain.food.dataclasses import FoodNutrientSource
from pii.domain.food.stores import FoodNutrientSourceStore_NoDB


class FoodNutrientSourceProfile(BaseProfile[FoodNutrientSource]):
    _store = FoodNutrientSourceStore_NoDB
    _import_mapping = {"id": "remote_id"}

    @classmethod
    def create(cls, record: dict, deep: bool = False) -> "FoodNutrientSourceProfile":
        source = cls.import_record(record, deep=deep)
        profile = cls()
        profile._store.put(source)
        profile._instance = source
        return profile

    @classmethod
    def import_record(cls, record: Union[dict, FoodNutrientSource], deep: bool = False) -> FoodNutrientSource:
        if isinstance(record, FoodNutrientSource):
            return record

        if not isinstance(record, dict):
            raise TypeError(f"Cannot import object of type {type(record)}")

        mapped = cls._apply_import_mapping(record, deep=deep)
        cleaned = cls()._recursive_remap(mapped)
        source = FoodNutrientSource(**cleaned)

        if deep and source.remote_id:
            store = cls._store()
            existing = store.get_by_remote_id(source.remote_id)
            if existing:
                return existing
            store.put(source)

        return source

    def update(self, obj: Union[dict, FoodNutrientSource], deep: bool = False) -> None:
        updated = self.import_record(obj, deep=deep)
        self._instance = updated
        self._store.put(updated)
