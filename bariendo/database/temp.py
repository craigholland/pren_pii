from bariendo.database.db_config import SEED_JSON_PATH
import json



import os
import ijson



def stream_food_records(path: str):
    """
    Generator that yields one food record at a time from a large JSON array.
    """
    with open(path, "rb") as f:
        for record in ijson.items(f, "item"):
            yield record


def main():
    if not os.path.exists(SEED_JSON_PATH):
        raise FileNotFoundError(f"JSON file not found at: {SEED_JSON_PATH}")

    print(f"Streaming records from {SEED_JSON_PATH}")
    target_columns = [
        'brandOwner',
        'dataSource',
        'brandedFoodCategory',
        'dataType',

    ]
    from collections import defaultdict
    data = defaultdict(list)


    for idx, food in enumerate(stream_food_records(SEED_JSON_PATH), start=1):
        # Example processing: print the description of each record
        for column in target_columns:
            data[column].append(food[column])

        # For testing, break after first 10 records
        # if idx >= 10:
        #     break
    for column in target_columns:
        data[column] = list(set(data[column]))

    for k,v in data.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
