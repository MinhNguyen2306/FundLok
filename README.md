# FundLok MVP Backend

API backend for the FundLok fintech platform — enabling SMEs to raise capital through revenue-share investments from accredited investors.

**Current status (March 2026)**  
Local development server running stably with basic user authentication and health endpoints.

## Features Implemented

- User registration (`POST /auth/register`)
- Simple email + password login (`POST /auth/login`) — returns JWT access token
- Protected user profile endpoint (`GET /users/me`)
- Health check (`GET /health`) and DB connectivity test (`GET /test-db`)
- Argon2 password hashing (secure, no length limit issues)
- Dependency injection for database sessions (SQLAlchemy + PostgreSQL)
- Swagger UI auto-generated at `/docs`

## Tech Stack

- Python 3.11
- FastAPI (API framework)
- SQLAlchemy 2.x (ORM)
- PostgreSQL (database)
- Argon2 (password hashing)
- JWT (authentication)
- Uvicorn (ASGI server)
- Pydantic v2 (data validation & settings)

## Local Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (local or Docker)
- Git

### Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/fundlok-backend.git
   cd fundlok-backend

2. **Create & activate virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate    # Mac/Linux
   
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   
4. **Set up environment variables**
Contact Admin for details, to be copied into .env in project root directory. 
   ```bash
   DATABASE_URL=postgresql+psycopg2://api_user:your_password@localhost:5432/fundlok_dev
   SECRET_KEY=super_secret_change_me_32_chars_or_more
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
5. **Start the server**

   ```bash
   python -m venv venv
   source venv/bin/activate    # Mac/Linux
   
6. **Open Swagger UI**

   ```bash
   http://127.0.0.1:8000/docs
   Register a user → login → copy token → click Authorize → paste Bearer [token] → test protected endpoints

## API smoke test script

End-to-end HTTP checks for all public and authenticated routes, in the correct dependency order (register → login → SME / investor / admin flows, files, loans, market, payments, admin audit).

**Prerequisites**

- API running (e.g. Uvicorn on `http://127.0.0.1:8000`).
- `.env` in the project root with a valid `DATABASE_URL` (the script updates KYC document rows in the DB after file uploads; same DB as the API).

**Run** (from the project root, with your virtualenv activated):

```bash
python scripts/test_all_endpoints.py
```

Optional environment variables:

- `FUNDL_API_BASE_URL` — default `http://127.0.0.1:8000`
- `FUNDL_API_PASSWORD` — default `TestPassw0rd!` (test users get unique emails per run)

## Database: idempotency columns & migrations

The ORM expects optional **idempotency** storage on:

| Table            | Column            | Purpose                                      |
|------------------|-------------------|----------------------------------------------|
| `orders`         | `idempotency_key` | `Idempotency-Key` on market listing orders   |
| `ledger_entries` | `idempotency_key` | `Idempotency-Key` on disbursements / repayments |

**Alembic** (when your DB role can create objects in `public` and run migrations):

```bash
alembic upgrade head
```

Revisions **`0002`** and **`0003`** add these columns and unique constraints. If Alembic cannot run (e.g. `permission denied for schema public`), a superuser can apply the same DDL manually; see `scripts/add_idempotency_columns.sql` for an idempotent `ALTER TABLE` / `CREATE UNIQUE INDEX` block you can append to your own DDL bundle.

**Grants:** the application DB user needs `USAGE` (and typically `CREATE` on `public` if you use Alembic there) so Alembic can create `alembic_version` and apply revisions.

## Project Structure
```
fundlok-backend/
├── scripts/                    # API smoke test, optional DDL helpers
├── alembic/                    # Database migrations (Alembic)
├── app/                        # Main application code
│   ├── auth/                   # Authentication endpoints & logic
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── core/                   # Shared config & database setup
│   │   ├── config.py
│   │   └── database.py
│   ├── projects/               # Project-related endpoints (to be expanded)
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── users/                  # User models & related logic
│   │   └── models.py
│   ├── utils/                  # Shared helpers (JWT, password hashing)
│   │   ├── jwt.py
│   │   └── password.py
│   └── main.py                 # FastAPI app entry point
├── db/                         # Database-related files (future)
│   ├── migrations/             # Alembic migration scripts (planned)
│   └── seeds/                  # Reference / lookup data SQL
├── tests/                      # Unit & integration tests (future)
├── .env.example                # Template for environment variables
├── requirements.txt            # Python dependencies
└── README.md                   # This file
