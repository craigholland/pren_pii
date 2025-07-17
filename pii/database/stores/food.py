from pii.database.store_adapters.sqlalchemy_store import BaseStoreSQLAlchemy
from typing import Any, Optional, TypeVar
from pii.database.models.food import (
    Food,
    Ingredient,
    Nutrient,
    FoodNutrientSource,
    FoodNutrientDerivation,
    FoodNutrient,
    LabelNutrients,
)

T = TypeVar("T")


class FoodStore(BaseStoreSQLAlchemy):
    _orm_model = Food


    def get_by_remote_id(self, remote_id: Any, pk: str = "remote_id") -> Optional[T]:
        return super().get_by_remote_id(remote_id, pk=pk)


class IngredientStore(BaseStoreSQLAlchemy):
    _orm_model = Ingredient

    def __init__(self):
        super().__init__()

    def get_by_remote_id(self, remote_id: Any, pk: str = "remote_id") -> Optional[T]:
        return super().get_by_remote_id(remote_id, pk=pk)


class NutrientStore(BaseStoreSQLAlchemy):
    _orm_model = Nutrient

    def __init__(self):
        super().__init__()

    def get_by_remote_id(self, remote_id: Any, pk: str = "remote_id") -> Optional[T]:
        return super().get_by_remote_id(remote_id, pk=pk)


class FoodNutrientSourceStore(BaseStoreSQLAlchemy):
    _orm_model = FoodNutrientSource

    def __init__(self):
        super().__init__()

    def get_by_remote_id(self, remote_id: Any, pk: str = "remote_id") -> Optional[T]:
        return super().get_by_remote_id(remote_id, pk=pk)


class FoodNutrientDerivationStore(BaseStoreSQLAlchemy):
    _orm_model = FoodNutrientDerivation

    def __init__(self):
        super().__init__()

    def get_by_remote_id(self, remote_id: Any, pk: str = "remote_id") -> Optional[T]:
        return super().get_by_remote_id(remote_id, pk=pk)


class FoodNutrientStore(BaseStoreSQLAlchemy):
    _orm_model = FoodNutrient

    def __init__(self):
        super().__init__()

    def get_by_remote_id(self, remote_id: Any, pk: str = "remote_id") -> Optional[T]:
        return super().get_by_remote_id(remote_id, pk=pk)


class LabelNutrientsStore(BaseStoreSQLAlchemy):
    _orm_model = LabelNutrients

    def __init__(self):
        super().__init__()

    def get_by_remote_id(self, remote_id: Any, pk: str = "remote_id") -> Optional[T]:
        return super().get_by_remote_id(remote_id, pk=pk)
