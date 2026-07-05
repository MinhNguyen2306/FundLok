# FundLok MVP Backend

API backend for the FundLok fintech platform. The app uses FastAPI, SQLAlchemy, Alembic, and PostgreSQL.

## Features

- User registration and login with JWT access and refresh tokens
- Protected user profile endpoint
- SME, investor, admin, files, loans, underwriting, contracts, market, and payments routes
- Swagger UI at `/docs`
- Alembic migrations for schema management

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Uvicorn
- Pydantic v2

## Local Development

### Prerequisites

- Python 3.11+
- Docker Desktop or Docker Engine with Compose
- Git
- [Bun](https://bun.sh) (optional) — for the `bun run` task shortcuts below

## Task scripts (Bun)

Common tasks are wrapped as `package.json` scripts. Run them with `bun run <script>`.
First-time setup: `bun run setup` (creates `venv` and installs dependencies), then
copy `.env.example` to `.env`.

The fast path for daily work:

```bash
bun run dev      # start Postgres/Mailpit/MinIO, then uvicorn --reload on :8000
```

| Command | What it does |
| --- | --- |
| `bun run setup` | Create `venv` and `pip install -r requirements.txt` |
| `bun run dev` | Start infra containers, then `uvicorn --reload` on **:8000** |
| `bun run start` | Start infra + `alembic upgrade head` + uvicorn on **:8000** (no reload) |
| `bun run reset` | Drop + recreate the local DB → migrate → seed (login password `Password123!`) |
| `bun run migrate` | `alembic upgrade head` |
| `bun run migrate:new "message"` | Autogenerate a new migration |
| `bun run seed` | Load `scripts/seed_data.sql` into the local DB |
| `bun run psql` | Open a `psql` shell to `fundlok_dev` |
| `bun run test` | Run `pytest -q` |
| `bun run up` / `down` / `stop` / `logs` | Manage the infra containers (Postgres, Mailpit, MinIO) |

Full-container run (builds the image and runs the API in Docker too, prod-like):

| Command | What it does |
| --- | --- |
| `bun run docker:up` | `docker compose up -d --build` — builds and runs **api + infra** (api on :8000; migrations run on boot) |
| `bun run docker:build` | Build just the api image |
| `bun run docker:down` | Stop everything |
| `bun run docker:logs` | Tail the api container logs |

Prefer `bun run dev` for day-to-day work (hot reload, runs on the host so `localhost`
reaches every container). Use `bun run docker:up` for a prod-like containerized run.

The manual, step-by-step equivalents are documented below.

### 1. Clone the repository

```bash
git clone <your-repo-url> FundLok
cd FundLok
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your local environment file

```bash
cp .env.example .env
```

Local development PostgreSQL URL:

```bash
postgresql+psycopg2://fundlok:fundlok@localhost:5433/fundlok_dev
```

If you later run the API inside Docker on the same Compose network, use:

```bash
postgresql+psycopg2://fundlok:fundlok@postgres:5432/fundlok_dev
```

### 5. Start PostgreSQL with Docker

```bash
docker compose up -d postgres
```

Check that the container is healthy:

```bash
docker compose ps
```

The container initializes the `pgcrypto` extension on first boot so Alembic migrations can use `gen_random_uuid()`.

### 6. Run database migrations

```bash
alembic upgrade head
```

### 7. Start the API

```bash
uvicorn app.main:app --reload
```

The API runs locally at:

```bash
http://127.0.0.1:8000
```

Swagger UI:

```bash
http://127.0.0.1:8000/docs
```

### Optional: seed reference data 

If you want sample data in the local database:

```bash
docker compose exec -T postgres psql -U fundlok -d fundlok_dev < scripts/Setup_Table_Inserts.sql
```

The seed file is useful for reference data and relationship testing. The API smoke test still creates fresh users dynamically.

## Common Docker Commands

Start PostgreSQL:

```bash
docker compose up -d postgres
```

View logs:

```bash
docker compose logs -f postgres
```

Stop containers:

```bash
docker compose down
```

Stop containers and remove the local database volume:

```bash
docker compose down -v
```

If you already created a database volume before the init SQL existed and see an error related to `gen_random_uuid()`, recreate the volume once with:

```bash
docker compose down -v
docker compose up -d postgres
```

## API Smoke Test Script

End-to-end HTTP checks for the public and authenticated routes are available in `scripts/test_all_endpoints.py`.

Prerequisites:

- The API is running locally, default `http://127.0.0.1:8000`
- `.env` exists in the project root with a valid `DATABASE_URL`

Run:

```bash
python scripts/test_all_endpoints.py
```

Optional environment variables:

- `FUNDL_API_BASE_URL` defaults to `http://127.0.0.1:8000`
- `FUNDL_API_PASSWORD` defaults to `TestPassw0rd!`

## Cloud Run Notes

For Cloud Run, set `DATABASE_URL` and `SECRET_KEY` in the service environment variables. If either value is missing, the app fails during import and the container never reaches the listening state.

## Project Structure

```text
FundLok/
├─ alembic/                     # Database migrations
├─ app/                         # Main application code
├─ docker/                      # Local Docker init scripts + container entrypoint
├─ scripts/                     # SQL helpers, smoke tests, reset_db.sh, seed_data.sql
├─ docker-compose.yml           # Local Postgres/Mailpit/MinIO + api service
├─ package.json                 # `bun run` task shortcuts
├─ main.py                      # Root entry point
├─ README.md
└─ requirements.txt
```
