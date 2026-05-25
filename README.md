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


1. **Install the DB**
   ```bash
   Create DB  docker exec -i postgres-dev psql -U postgres < CreateDB_DDL.sql
   Create Tables docker exec -i postgres-dev psql -U edwardw -d fundlok_dev < DDL.sql
   Insert test data docker exec -i postgres-dev psql -U edwardw -d fundlok_dev < Setup_Table_Inserts.sql
2. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/fundlok-backend.git
   cd fundlok-backend

3. **Create & activate virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate    # Mac/Linux
   
4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   
5. **Set up environment variables**
Contact Admin for details, to be copied into .env in project root directory. 
   ```bash
   DATABASE_URL=postgresql+psycopg2://api_user:your_password@localhost:5432/fundlok_dev
   SECRET_KEY=super_secret_change_me_32_chars_or_more
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
6. **Start the server**

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8080 --reload
   ```

   For Cloud Run, set `DATABASE_URL` and `SECRET_KEY` in the service environment variables. If either one is missing, the app fails during import and the container never reaches the listening state.

7. **Open Swagger UI**

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
FundLok/
├─ alembic/                     # Database migrations (Alembic)
│  ├─ env.py
│  ├─ README
│  ├─ script.py.mako
│  └─ versions/                 # Alembic migration scripts
│     └─ 0001_initial_schema.py
├─ alembic.ini                  # Configuration for Alembic migrations
├─ app/                         # Main application code
│  ├─ admin/                    # Administrative management endpoints
│  ├─ auth/                     # Authentication endpoints & logic
│  │  ├─ router.py
│  │  ├─ schemas.py
│  │  └─ service.py
│  ├─ contracts/                # Contract management and generation services
│  ├─ core/                     # Shared config & database setup
│  │  ├─ config.py              # Application settings and configuration
│  │  └─ database.py            # Database connection and session management
│  ├─ files/                    # File handling services (e.g., KYC uploads)
│  ├─ lending/                  # Core lending and KYC logic
│  ├─ loans/                    # Loan processing and management logic
│  ├─ main.py                   # FastAPI app entry point
│  ├─ market/                   # Secondary market listings and orders
   uvicorn main:app --host 0.0.0.0 --port 8080 --reload
│  ├─ projects/                 # Project-related endpoints (to be expanded)

   Cloud Run must also receive `DATABASE_URL` and `SECRET_KEY` as service environment variables. If either one is missing, the app fails during import and the container never reaches the listening state.
│  ├─ schemas/                  # Data validation and Pydantic settings
│  ├─ sme/                      # SME-specific business workflows
│  ├─ underwriting/             # Risk assessment and underwriting logic
│  ├─ users/                    # User models & related logic
│  │  ├─ models.py              # User database models
│  │  └─ router.py
│  └─ utils/                    # Shared helpers (JWT, password hashing)
│     ├─ audit.py               # Audit logging utilities
│     ├─ jwt.py                 # JWT token generation and validation
│     ├─ password.py            # Password hashing (Argon2) and security
│     └─ rbac.py                # Role-based access control logic
├─ scripts/                     # API smoke tests and DDL helpers
│  ├─ CreateDB_DDL.sql          # Database creation DDL script
│  ├─ DDL.sql                   # Table structure definition script
│  ├─ Setup_Table_Inserts.sql   # Reference and test data SQL
│  └─ test_all_endpoints.py     # End-to-end API smoke test script
├─ ci_test.txt                  # CI test logs or status
├─ main.py                      # Root level execution script
├─ README.md                    # Project documentation
└─ requirements.txt             # Python project dependencies

```