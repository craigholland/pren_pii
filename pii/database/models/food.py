from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Date, Boolean, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from bariendo.database.models.core.service_object import ServiceObject, ServiceObjectDC
from bariendo.database.models.core.main import db
from bariendo.domain.food.dataclasses import (
    Food as FoodDC,
    FoodNutrient as FoodNutrientDC,
    FoodNutrientSource as FoodNutrientSourceDC,
    FoodNutrientDerivation as FoodNutrientDerivationDC,
    Nutrient as NutrientDC,
    LabelNutrients as LabelNutrientsDC,
    Ingredient as IngredientDC
)
# ----------- Association Tables -----------
class FoodIngredientAssoc(ServiceObject, db.Model):
    __tablename__ = 'food_ingredient_assoc'

    food_id = Column(UUID, ForeignKey('foods.id', ondelete='CASCADE'), primary_key=True)
    ingredient_id = Column(UUID, ForeignKey('ingredients.id', ondelete='CASCADE'), primary_key=True)

    food = relationship('Food', back_populates='food_ingredient_assocs', lazy='joined')
    ingredient = relationship('Ingredient', back_populates='food_ingredient_assocs', lazy='joined')

# ------------- Association table (M:M with extra column) -------------
class FoodNutrientAssoc(ServiceObject, db.Model):
    __tablename__ = "food_nutrient_assoc"

    food_id           = Column(UUID, ForeignKey("foods.id",           ondelete="CASCADE"), primary_key=True)
    food_nutrient_id  = Column(UUID, ForeignKey("food_nutrients.id",  ondelete="CASCADE"), primary_key=True)
    amount            = Column(Float, nullable=False)        # amount is *per Food*

    food              = relationship("Food",         back_populates="food_nutrient_assocs", lazy="joined")
    food_nutrient     = relationship("FoodNutrient", back_populates="food_nutrient_assocs", lazy="joined")


# ----------- Core Models -----------
class Food(ServiceObjectDC, db.Model):
    __tablename__ = 'foods'
    __dataclass__ = FoodDC

    remote_id = Column(Integer, unique=True, nullable=False, index=True)
    branded_food_category = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    brand_owner = Column(String, nullable=True)
    gtin_upc = Column(String, nullable=True)
    serving_size = Column(Float, nullable=True)
    serving_size_unit = Column(String, nullable=True)
    household_serving = Column(String, nullable=True)
    household_serving_unit = Column(String, nullable=True)
    publication_date = Column(Date, nullable=True)

    # --- Ingredients M:M
    food_ingredient_assocs = relationship(
        "FoodIngredientAssoc", back_populates="food",
        cascade="all, delete-orphan", lazy="joined"
    )
    ingredients = association_proxy(
        "food_ingredient_assocs", "ingredient",
        creator=lambda ing: FoodIngredientAssoc(
            ingredient=ServiceObjectDC.from_dataclass(ing)
        )
    )

    # --- FoodNutrients M:M
    food_nutrient_assocs = relationship(
        "FoodNutrientAssoc", back_populates="food",
        cascade="all, delete-orphan", lazy="joined"
    )
    food_nutrients = association_proxy(
        "food_nutrient_assocs", "food_nutrient",
        creator=lambda fn: FoodNutrientAssoc(
            food_nutrient=ServiceObjectDC.from_dataclass(fn)
        )
    )

    # --- LabelNutrients 1:1
    label_nutrients = relationship(
        "LabelNutrients", back_populates="food",
        uselist=False, cascade="all, delete-orphan", lazy="joined"
    )

class Ingredient(ServiceObjectDC, db.Model):
    __tablename__ = 'ingredients'
    __dataclass__ = IngredientDC

    remote_id = Column(Integer, unique=True, nullable=True)
    name = Column(String, nullable=False)
    is_organic = Column(Boolean, default=False)

    food_ingredient_assocs = relationship(
        'FoodIngredientAssoc', back_populates='ingredient', cascade='all, delete-orphan', lazy='joined'
    )
    foods = association_proxy(
        'food_ingredient_assocs', 'food',
        creator=lambda food: FoodIngredientAssoc(food=ServiceObjectDC.from_dataclass(food))
    )

class FoodNutrient(ServiceObjectDC, db.Model):
    __tablename__ = 'food_nutrients'
    __dataclass__ = FoodNutrientDC

    remote_id = Column(Integer, unique=True, nullable=True)
    nutrient_id = Column(UUID, ForeignKey("nutrients.id", ondelete="CASCADE"), nullable=False)
    derivation_id = Column(UUID, ForeignKey("food_nutrient_derivation.id", ondelete="SET NULL"), nullable=True)

    # --- relationships
    nutrient = relationship("Nutrient", back_populates="food_nutrients", lazy="joined")
    derivation = relationship("FoodNutrientDerivation", back_populates="food_nutrients", lazy="joined")

    food_nutrient_assocs = relationship(
        "FoodNutrientAssoc", back_populates="food_nutrient",
        cascade="all, delete-orphan", lazy="joined"
    )
    foods = association_proxy("food_nutrient_assocs", "food")


class Nutrient(ServiceObjectDC, db.Model):
    __tablename__ = 'nutrients'
    __dataclass__ = NutrientDC

    remote_id = Column(Integer, unique=True, nullable=True)
    number = Column(String, nullable=True)
    name = Column(String, nullable=False)
    rank = Column(Integer, nullable=True)
    unitname = Column(String, nullable=True)

    food_nutrients = relationship(
        "FoodNutrient", back_populates="nutrient",
        cascade="all, delete-orphan", lazy="joined"
    )

class FoodNutrientSource(ServiceObjectDC, db.Model):
    __tablename__ = 'food_nutrient_source'
    __dataclass__ = FoodNutrientSourceDC

    remote_id = Column(Integer, unique=True, nullable=False, index=True)
    code = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    derivations = relationship(
        'FoodNutrientDerivation', back_populates='source', cascade='all, delete-orphan', lazy='joined'
    )

class FoodNutrientDerivation(ServiceObjectDC, db.Model):
    __tablename__ = 'food_nutrient_derivation'
    __dataclass__ = FoodNutrientDerivationDC

    code = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    source_id = Column(
        UUID,
        ForeignKey('food_nutrient_source.id', ondelete='CASCADE'),
        nullable=True
    )

    source = relationship('FoodNutrientSource', back_populates='derivations', lazy='joined')
    food_nutrients = relationship('FoodNutrient', back_populates='derivation', lazy='joined')

class LabelNutrients(ServiceObjectDC, db.Model):
    __tablename__ = 'label_nutrients'
    __dataclass__ = LabelNutrientsDC

    food_id = Column(UUID, ForeignKey('foods.id', ondelete='CASCADE'), unique=True, nullable=True)
    remote_id = Column(Integer, unique=True, nullable=True)

    fat = Column(Float, nullable=False)
    saturated_fat = Column(Float, nullable=False)
    trans_fat = Column(Float, nullable=False)
    cholesterol = Column(Float, nullable=False)
    sodium = Column(Float, nullable=False)
    carbohydrates = Column(Float, nullable=False)
    fiber = Column(Float, nullable=False)
    sugars = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    calcium = Column(Float, nullable=False)
    iron = Column(Float, nullable=False)
    calories = Column(Float, nullable=False)

    food = relationship('Food', back_populates='label_nutrients', lazy='joined')
