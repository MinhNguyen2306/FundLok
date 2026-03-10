FundLok MVP 🚀
CTO Note: This is the core FastAPI backend for FundLok. This repository contains the source code, dependency requirements, and configuration templates needed to run the MVP locally or in a containerized environment.

🛠 Tech Stack
Framework: FastAPI (Python 3.11+)

Database: PostgreSQL

Data Validation: Pydantic Settings

Server: Uvicorn

🚀 Local Setup Guide
Follow these steps to get your local development environment running.

1. Clone the Repository
Bash
git clone https://github.com/MinhNguyen2306/FundLok.git
cd FundLok
2. Configure Virtual Environment
Bash
# Create the environment
python3 -m venv venv

# Activate the environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
3. Environment Variables
The application requires a .env file in the root directory to handle secrets and database connections.

Create a .env file: touch .env

Add the following required fields:

Plaintext
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/<db_name>
SECRET_KEY=your_secure_random_secret_key
(Refer to .env.example for the full list of required configuration keys).

🏃 Running the Application
Launch the development server using Uvicorn. Note that the entry point is located within the app subdirectory.

Bash
uvicorn app.main:app --reload
📍 API Endpoints & Documentation
Once the server is running, you can access the interactive documentation at:

Swagger UI (Interactive): http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc

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
