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

📂 Project Structure
Plaintext
.
├── app/                # Main application package
│   ├── core/           # Config, database, and security logic
│   ├── api/            # Route handlers (Endpoints)
│   ├── models/         # Database models
│   └── main.py         # FastAPI app initialization
├── .gitignore          # Protected files (venv, .env, __pycache__)
├── .env.example        # Template for environment variables
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
