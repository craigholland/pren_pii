# Bariendo

A simple food-and-nutrition database backend and diet recommendation tool powered by Docker Compose, Poetry, and Alembic.

---

## Assignment Overview

**Nutrition and Diet Recommendation Tool**  
Build an app for dietitians and health-conscious consumers to:
- **Search** USDA FoodData Central for common foods  
- **View basic nutritional facts** (calories, protein, fat, carbs)  
- **Manage a list of favorites** or ingredients  
- _(Optional)_ Add one extra feature (e.g. AI chatbot, visualizations, meal planning, performant API)

---

## Prerequisites

1. **Git**  
2. **Docker & Docker Compose**  
   - Docker Desktop (Windows/macOS) or Docker Engine + Docker Compose (Linux)  
   - Verify:
     ```bash
     docker --version
     docker-compose --version
     ```
3. **Poetry**  
   - Install via [https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation)  
   - Verify:
     ```bash
     poetry --version
     ```

---

## 1. Clone the Repository

```bash
git clone git@github.com:craigholland/bariendo.git
cd bariendo
```

---

## 2. Install Python Dependencies

```bash
poetry install
```

This creates an isolated virtual environment and installs all required packages.

---

## 3. Configure the Database

Open `bariendo/database/db_config.py` and review:

```python
DB_IMAGE           = "postgres:15"
DB_CONTAINER_NAME  = "bariendo-db"
DB_USER            = "bariendo_user"
DB_PASSWORD        = "securepassword"
DB_NAME            = "bariendo"
SEED_DATA_FILENAME = "nutrient_data.json"
SEED_DATA_PATH     = Path(__file__).parent / "data"
```

1. **Adjust** these values to match your environment.  
2. **Place your seed file** (e.g. `nutrient_data.json`, >3 GB) in:
   ```
   bariendo/database/data/
   ```
   > **Note:** We seed only the first 500 records by default for quick startup. Full seeding (~450 000 records) is possible but may take hours.

---

## 4. Start the Database & Seed Data

```bash
chmod +x bariendo/database/bin/start_db.sh
./bariendo/database/bin/start_db.sh
```

What this does:
1. Spins up PostgreSQL via Docker Compose  
2. Runs Alembic migrations  
3. Seeds the first 500 records from your JSON file

---

## 5. Tear Down / Reset the Database

```bash
chmod +x bariendo/database/bin/nuke_db.sh
./bariendo/database/bin/nuke_db.sh
```

---

## Approach and Key Design Decisions

- **Poetry & Docker Compose** for reproducible environments and dependency isolation.  
- **Alembic** for schema migrations—keeps database evolution under version control.  
- **JSON seed file** (USDA FoodData Central subset) loaded via a small custom script—allows you to swap or subset data without rebuilding images.  
- **Shell scripts** (`start_db.sh`, `nuke_db.sh`) wrap the common workflows and make onboarding as simple as:
  1. Grant execute permission  
  2. Run the script  
- **Configurable** via `db_config.py`—all Docker-related settings, filenames, and paths live in one place.  
- **Speed vs completeness** trade-off: seed only 500 records by default to get up and running in minutes; full dataset seeding is opt-in.

---

## What I’d Improve or Expand with More Time

1. **Backend API**  
   - Expose REST or GraphQL endpoints for search, detail retrieval, and favorites management  
   - Pagination, filtering, and caching for performant queries  

2. **Frontend/UI**  
   - Simple web interface (React/Vue) for dietitians and consumers  
   - Nutritional breakdown visualizations (pie charts, bar graphs)  

3. **Favorites & Meal Plans**  
   - Allow users to save favorites and assemble simple meal plans  
   - Aggregate nutritional totals per meal/day  

4. **Optional Advanced Feature**  
   - **AI Chatbot**: Integrate an LLM (Anthropic API) to answer diet-related questions  
   - **Insights**: Surface data trends (e.g., “Top 10 highest-protein foods”)  

5. **Dataset Flexibility**  
   - Fetch directly from USDA API for branded subsets  
   - Incremental seeding or background job to load full dataset without blocking startup  

6. **Testing & CI**  
   - Unit and integration tests for migrations, seed logic, and API  
   - GitHub Actions to lint, test, and build images on each push

---

## Submission

- Private GitHub repo: share with **bariendo-dev**  
- Includes this README, committed code, and meaningful commit history.  
- Ready for further feature work or production hardening.
