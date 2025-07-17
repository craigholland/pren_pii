from typing import Optional, Union

from pii.common.abstracts.base_profile import BaseProfile
from pii.domain.food.dataclasses import Nutrient
from pii.domain.food.stores import NutrientStore_NoDB


class NutrientProfile(BaseProfile[Nutrient]):
    _store = NutrientStore_NoDB
    _import_mapping = {"id": "remote_id", "unitName": "unitname"}

    @classmethod
    def create(cls, record: dict, deep: bool = False) -> "NutrientProfile":
        nutrient = cls.import_record(record, deep=deep)
        profile = cls()
        profile._store.put(nutrient)
        profile._instance = nutrient
        return profile

    @classmethod
    def import_record(cls, record: Union[dict, Nutrient], deep: bool = False) -> Nutrient:
        if isinstance(record, Nutrient):
            return record

        if not isinstance(record, dict):
            raise TypeError(f"Cannot import object of type {type(record)}")

        mapped = cls._apply_import_mapping(record, deep=deep)
        cleaned = cls()._recursive_remap(mapped)
        nutrient = Nutrient(**cleaned)

        if deep and nutrient.remote_id:
            store = cls._store()
            existing = store.get_by_remote_id(nutrient.remote_id)
            if existing:
                store.delete(existing.id)
            store.put(nutrient)

        return nutrient

    def update(self, obj: Union[dict, Nutrient], deep: bool = False) -> None:
        updated = self.import_record(obj, deep=deep)
        self._instance = updated
        self._store.put(updated)
