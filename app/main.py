from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware  # ✅ Correct
from dotenv import load_dotenv

from app.routers import about
from .database import engine, Base
from .routers import auth, programs, media, contact, volunteers, events, donations
from fastapi.staticfiles import StaticFiles
import os

# Load environment variables from .env file
load_dotenv()

from sqlalchemy import text

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[Startup Warning] Error during create_all: {e}")

# Automatically ensure all PayHero donation columns exist
try:
    with engine.begin() as conn:
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE paymentstatus AS ENUM ('PENDING', 'QUEUED', 'SUCCESS', 'FAILED');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;

            ALTER TABLE donations ADD COLUMN IF NOT EXISTS donor_phone VARCHAR;
            ALTER TABLE donations ADD COLUMN IF NOT EXISTS message TEXT;
            ALTER TABLE donations ADD COLUMN IF NOT EXISTS payment_status paymentstatus DEFAULT 'PENDING';
            ALTER TABLE donations ADD COLUMN IF NOT EXISTS external_reference VARCHAR;
            ALTER TABLE donations ADD COLUMN IF NOT EXISTS payhero_reference VARCHAR;
            ALTER TABLE donations ADD COLUMN IF NOT EXISTS provider_reference VARCHAR;
            ALTER TABLE donations ADD COLUMN IF NOT EXISTS payment_provider VARCHAR DEFAULT 'm-pesa';
            ALTER TABLE donations ADD COLUMN IF NOT EXISTS transaction_date TIMESTAMP WITH TIME ZONE;
            ALTER TABLE donations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;
            CREATE INDEX IF NOT EXISTS ix_donations_external_reference ON donations (external_reference);
        """))
    print("[Startup] Donations table schema synchronized successfully.")
except Exception as e:
    print(f"[Startup Warning] Error syncing donations schema: {e}")

from app.utils.storage import get_static_dir, STATIC_DIR

# Ensure static directories exist
for folder in ["media", "programs", "team", "impact"]:
    get_static_dir(folder)

app = FastAPI(
    title="Nawiri EmpowerHub API",
    description="Backend for the Nawiri EmpowerHub Website.",
    version="1.0.0"
)

# Allow frontend origins
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000",
    "https://frontend-seven-gamma-38.vercel.app",
    "https://www.nawiriempowerhub.org",
    "https://nawiriempowerhub.org",
    "https://vercel.com/elvis-marubes-projects/nawiri-empowerhub/3AFd7Zd9pqYP2BmMKW4SnRzTzLYZ",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.vercel\.app)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all the routers
app.include_router(auth.router)
app.include_router(programs.router)
app.include_router(media.router)
app.include_router(contact.router)
app.include_router(volunteers.router)
app.include_router(events.router)
app.include_router(about.router)
app.include_router(donations.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Nawiri EmpowerHub API"}

# Ensure static path works on local dev and Railway /app/static volume mount
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")