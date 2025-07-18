# Prenuvo PII Service

A modular, testable, and domain-driven Python backend for managing Personally Identifiable Information (PII) with strict type safety, UUID-based identifiers, and support for both database-backed and in-memory stores.

---

## 🔧 Project Structure

This project adheres to **Clean Architecture** and SOLID principles:

```
pii/
├── common/          # Abstract base classes, utilities, type enforcement
├── domain/          # Pure dataclasses (no dependencies)
├── database/        # SQLAlchemy models, migration scripts, and store adapters
```

---

## 🚀 Quickstart

### 1. Clone the Repository

```bash
git clone https://github.com/craigholland/pren_pii.git
cd pren_pii
```

---

### 2. Install Poetry

Make sure you have [Poetry](https://python-poetry.org/docs/#installation) installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Then make sure it's on your PATH:

```bash
poetry --version
```

> ⚠️ Python 3.12 is required. You can use [pyenv](https://github.com/pyenv/pyenv) or another tool to manage versions.

---

### 3. Install Dependencies

```bash
poetry install
```

This will create a virtual environment and install all dependencies defined in `pyproject.toml`.

To activate the virtual environment:

```bash
poetry shell
```

---

### 4. Set Up the Database (PostgreSQL + Alembic)

#### Spin up PostgreSQL via Docker

```bash
./pii/database/bin/start_db.sh
```

This will:
- Launch a local PostgreSQL container (`pren_pii_postgres`)
- Mount a named volume for persistence
- Default port: `5432`
- Database name: `pren_pii`
- User: `craig` | Password: `craig`

> You can change these values in the `.env` file in the `pii/database/` directory.

---

### 5. Run Migrations

```bash
cd pii/database/
poetry run alembic upgrade head
```

This will apply all current migration scripts from the `migrations/` folder and set up the schema.

---

### 6. Running Tests

> Not yet implemented, but the architecture is fully test-ready. Coming soon.

---

## 🧠 Design Philosophy

- **Domain-Driven**: Business rules live in pure dataclasses with zero external dependencies.
- **Pluggable Storage**: Swap in-memory stores and SQLAlchemy-backed stores without changing the domain logic.
- **Validator Support**: All ORM models may define `__validator__` to register custom pre-commit logic.
- **Typed UUIDs**: Primary keys and foreign keys are all UUID strings, enforced both in the DB and dataclass layer.
- **RelationshipList**: Custom `RelationshipList[T]` type allows introspection and recursive type checking on 1:M relationships.

---

## 📁 Directory Reference

| Directory | Purpose |
|----------|---------|
| `pii/common/` | Base classes (`BaseDataclass`, `BaseStore`, `BaseProfile`, etc.) |
| `pii/domain/` | Pure dataclass definitions of core entities |
| `pii/database/` | SQLAlchemy models, migration scripts, and database bootstrapping logic |
| `pii/database/models/core/validators/` | Optional validation logic for domain entities |

---

## 🗺️ Roadmap

- ✅ Clean alignment of domain, common, and database layers  
- ⏳ Add unit and integration tests  
- ⏳ Implement profile and store logic for key entities  
- ⏳ Introduce service orchestration (interfaces, lifecycle hooks)  
- ⏳ Logging, CLI entrypoints, and dev tools

---

## 🧪 Dev Notes

- Uses UUID strings, not native `uuid.UUID` objects, to simplify JSON serialization and DB compatibility.
- Validators are modular and dynamically invoked if a model defines `__validator__`.
- To inspect database objects and relationships, use any PostgreSQL GUI (e.g., [pgAdmin](https://www.pgadmin.org/) or [DataGrip](https://www.jetbrains.com/datagrip/)).

---

## 🧑‍💻 Author

**Craig Holland**
