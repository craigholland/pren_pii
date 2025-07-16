import os

# Allow override via .env or environment for flexibility
DB_USER = os.getenv("POSTGRES_USER", "bariendo")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "bariendo")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "bariendo")
DB_CONNECT_TIMEOUT = 5

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Path to the USDA JSON file
SEED_JSON_PATH = os.getenv(
    "SEED_JSON_PATH",
    os.path.join(os.path.dirname(__file__), "data", "FoodData_Central_branded_food_json_2025-04-24.json")
)
SEED_JSON_TOTAL_RECORDS = 452998
DEFAULT_RECORD_LIMIT = 500