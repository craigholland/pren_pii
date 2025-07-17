import os
import ijson
import argparse
from tqdm import tqdm
from sqlalchemy.exc import IntegrityError
from pii.database.models.core.main import db
from pii.database.db_config import SEED_JSON_PATH, SEED_JSON_TOTAL_RECORDS, DEFAULT_RECORD_LIMIT
from pii.database.models.food import (
    Food,
    Ingredient,
    FoodIngredientAssoc,
    Nutrient,
    FoodNutrient,
    FoodNutrientDerivation,
    FoodNutrientSource,
    FoodNutrientAssoc,
    LabelNutrients,
)

def stream_food_records(path: str):
    with open(path, "rb") as f:
        for record in ijson.items(f, "item"):
            yield record

def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    params = dict(kwargs)
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    return instance

def seed_label_nutrients(session, food, ln_data):
    with session.no_autoflush:
        ln = session.query(LabelNutrients).filter_by(food_id=food.id).first()
    if not ln:
        ln = LabelNutrients(
            food=food,
            fat=ln_data.get('fat', {}).get('value', 0),
            saturated_fat=ln_data.get('saturatedFat', {}).get('value', 0),
            trans_fat=ln_data.get('transFat', {}).get('value', 0),
            cholesterol=ln_data.get('cholesterol', {}).get('value', 0),
            sodium=ln_data.get('sodium', {}).get('value', 0),
            carbohydrates=ln_data.get('carbohydrates', {}).get('value', 0),
            fiber=ln_data.get('fiber', {}).get('value', 0),
            sugars=ln_data.get('sugars', {}).get('value', 0),
            protein=ln_data.get('protein', {}).get('value', 0),
            calcium=ln_data.get('calcium', {}).get('value', 0),
            iron=ln_data.get('iron', {}).get('value', 0),
            calories=ln_data.get('calories', {}).get('value', 0),
        )
        session.add(ln)

def seed_ingredients(session, food, ingredients_str):
    for raw in ingredients_str.split(','):
        name = raw.strip()
        if not name:
            continue
        ingredient = get_or_create(session, Ingredient, name=name)
        with session.no_autoflush:
            assoc_exists = session.query(FoodIngredientAssoc).filter_by(
                food_id=food.id, ingredient_id=ingredient.id
            ).first()
        if not assoc_exists:
            food.ingredients.append(ingredient)

def seed_food_nutrients(session, food, food_nutrients):
    for fn in food_nutrients:
        nutr = fn.get('nutrient', {})
        if not all([nutr.get(k) for k in ('id', 'number', 'name', 'unitName')]):
            continue

        nutrient = get_or_create(session, Nutrient, remote_id=nutr['id'], defaults={
            'number': nutr['number'],
            'name': nutr['name'],
            'rank': nutr.get('rank'),
            'unitname': nutr['unitName'],
        })
        session.flush()  # Ensure nutrient.id is populated

        src = fn.get('foodNutrientDerivation', {}).get('foodNutrientSource', {})
        source = get_or_create(session, FoodNutrientSource, remote_id=src.get('id'), code=src.get('code'), defaults={'description': src.get('description')})
        session.flush()

        deriv_data = fn.get('foodNutrientDerivation', {})
        derivation = session.query(FoodNutrientDerivation).filter_by(source_id=source.id, code=deriv_data.get('code')).first()
        if not derivation:
            derivation = FoodNutrientDerivation(source=source, code=deriv_data.get('code'), description=deriv_data.get('description'))
            session.add(derivation)
            session.flush()

        with session.no_autoflush:
            existing_fn = session.query(FoodNutrient).filter_by(food_id=food.id, remote_id=fn['id']).first()

        if not existing_fn:
            food_nutrient = FoodNutrient(
                food_id=food.id,
                nutrient_id=nutrient.id,
                derivation_id=derivation.id,
                amount=fn.get('amount'),
                remote_id=fn['id']
            )
            session.add(food_nutrient)


def seed_food_record(session, record: dict):
    food = get_or_create(session, Food, remote_id=record['fdcId'])
    food.branded_food_category = record.get('brandedFoodCategory')
    food.description = record.get('description')
    food.brand_owner = record.get('brandOwner')
    food.gtin_upc = record.get('gtinUpc')
    food.serving_size = record.get('servingSize')
    food.serving_size_unit = record.get('servingSizeUnit')

    raw_hh = record.get('householdServingFullText')
    if raw_hh:
        parts = raw_hh.strip().split(None, 1)
        try:
            food.household_serving = float(parts[0])
        except (ValueError, IndexError):
            food.household_serving = None
        food.household_serving_unit = parts[1] if len(parts) > 1 else None

    food.publication_date = record.get('publicationDate')

    seed_label_nutrients(session, food, record.get('labelNutrients', {}))
    seed_ingredients(session, food, record.get('ingredients', ''))
    seed_food_nutrients(session, food, record.get('foodNutrients', []))

def main():
    parser = argparse.ArgumentParser(description="Seed the database from USDA JSON.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-f', '--full', action='store_true', help='Seed all records')
    group.add_argument('-r', '--record', type=int, help='Number of records to seed')
    args = parser.parse_args()

    limit = args.record if args.record is not None else SEED_JSON_TOTAL_RECORDS if args.full else DEFAULT_RECORD_LIMIT

    records = stream_food_records(SEED_JSON_PATH)
    if limit != SEED_JSON_TOTAL_RECORDS:
        import itertools
        records = itertools.islice(records, limit)

    spinner = tqdm(records, desc="Seeding foods", total=limit)
    for record in spinner:
        with db.Session() as session:
            try:
                seed_food_record(session, record)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error seeding fdcId={record.get('fdcId')}: {e}")

if __name__ == '__main__':
    main()
