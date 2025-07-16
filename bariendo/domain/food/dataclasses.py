# bariendo/domain/food/dataclasses.py

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from bariendo.common.abstracts.base_dataclass import BaseDataclass, RelationshipList

@dataclass
class Ingredient(BaseDataclass):
    id: Optional[str]        = None
    name: Optional[str]       = None
    is_organic: Optional[bool]= None

@dataclass
class Nutrient(BaseDataclass):
    id: Optional[str]        = None
    remote_id: Optional[int]  = None
    number: Optional[str]     = None
    name: Optional[str]       = None
    rank: Optional[int]       = None
    unitname: Optional[str]   = None

@dataclass
class FoodNutrientSource(BaseDataclass):
    id: Optional[str]        = None
    remote_id: Optional[int]  = None
    code: Optional[str]       = None
    description: Optional[str]= None

@dataclass
class FoodNutrientDerivation(BaseDataclass):
    id: Optional[str]        = None
    code: Optional[str]       = None
    description: Optional[str]= None
    source: Optional[FoodNutrientSource] = None

@dataclass
class FoodNutrient(BaseDataclass):
    id: Optional[str]        = None
    remote_id: Optional[int]  = None
    nutrient: Optional[Nutrient]            = None
    amount: Optional[float]   = None
    derivation: Optional[FoodNutrientDerivation] = None

@dataclass
class LabelNutrients(BaseDataclass):
    id: Optional[str]        = None
    fat: Optional[float]      = None
    saturated_fat: Optional[float] = None
    trans_fat: Optional[float] = None
    cholesterol: Optional[float] = None
    sodium: Optional[float]   = None
    carbohydrates: Optional[float] = None
    fiber: Optional[float]    = None
    sugars: Optional[float]   = None
    protein: Optional[float]  = None
    calcium: Optional[float]  = None
    iron: Optional[float]     = None
    calories: Optional[float] = None

@dataclass
class Food(BaseDataclass):
    id: Optional[str]               = None
    remote_id: Optional[int]         = None
    description: Optional[str]       = None
    branded_food_category: Optional[str] = None
    brand_owner: Optional[str]       = None
    gtin_upc: Optional[str]          = None
    serving_size: Optional[float]    = None
    serving_size_unit: Optional[str] = None
    household_serving: Optional[float]       = None
    household_serving_unit: Optional[str]    = None
    publication_date: Optional[date] = None

    # 1:M relationships default to empty lists
    ingredients: RelationshipList[Ingredient]    = field(default_factory=list)
    nutrients:   RelationshipList[FoodNutrient]  = field(default_factory=list)

    # 1:1 relationship remains Optional
    label_nutrients: Optional[LabelNutrients] = None
