# Nawiri EmpowerHub API

This is the backend API for the Nawiri EmpowerHub Website, providing essential services to manage programs, events, volunteers, media, contacts, and about sections.

## Tech Stack

*   **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
*   **Database:** PostgreSQL with [SQLAlchemy](https://www.sqlalchemy.org/) ORM
*   **Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
*   **Authentication:** JWT (JSON Web Tokens) using `python-jose` and `passlib`
*   **Media Storage:** Cloudinary & Local Static Files

## Features

*   **Authentication:** Secure token-based user authentication.
*   **Programs Management:** CRUD operations for initiatives and programs.
*   **Events Management:** Scheduling and managing organizational events.
*   **Volunteers Management:** Handling volunteer applications and data.
*   **Media Management:** Uploading and serving images/media files with Cloudinary support.
*   **Contact/Inquiries:** Handling contact forms and user inquiries.
*   **About Section:** Managing organization details, team members, and impact statistics.

## Prerequisites

*   Python 3.11+
*   PostgreSQL installed and running

## Installation

1.  **Navigate to the project directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    *   **Windows:**
        ```bash
        venv\Scripts\activate
        ```
    *   **Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Environment Variables

Create a `.env` file in the root directory based on your environment. Here is an example of what it might contain:

```env
# Database configuration


# JWT settings
SECRET_KEY=your_super_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cloudinary Setup
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

*(Note: Ensure you update these variables according to your actual local or production setup.)*

## Database Setup & Migrations

The project uses SQLAlchemy for models and Alembic for schema migrations.

1. Ensure your PostgreSQL database is running and matches the `DATABASE_URL` in your `.env` file.
2. Apply existing migrations to the database:
   ```bash
   alembic upgrade head
   ```
   *(Note: The FastAPI app is also configured to create tables on startup if they don't exist via `Base.metadata.create_all`, but `alembic upgrade head` is recommended to maintain migration history.)*

If you make any changes to the models in `app/models.py`, you can generate a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

## Running the Application

Start the development server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Documentation

FastAPI automatically generates interactive API documentation. Once the server is running, you can access them at:

*   **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
*   **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Project Structure

```text
backend/
├── alembic/             # Database migration scripts
├── app/                 # Main application directory
│   ├── routers/         # API route handlers (endpoints)
│   ├── services/        # Business logic and external integrations
│   ├── static/          # Local static file storage
│   ├── utils/           # Helper functions and utilities
│   ├── database.py      # Database connection and session management
│   ├── dependencies.py  # FastAPI dependencies (e.g., get_db)
│   ├── main.py          # FastAPI application entry point
│   ├── models.py        # SQLAlchemy database models
│   └── schemas.py       # Pydantic models (data validation/serialization)
├── .env                 # Environment variables (ignored in git)
├── alembic.ini          # Alembic configuration
├── Procfile             # Deployment configuration (e.g., for Heroku/Railway)
├── README.md            # Project documentation
└── requirements.txt     # Python dependencies
```
