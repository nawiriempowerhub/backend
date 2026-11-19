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

# Create database tables
Base.metadata.create_all(bind=engine)

from app.utils.storage import get_static_dir, STATIC_DIR

# Ensure static directories exist
for folder in ["media", "programs", "team", "impact"]:
    get_static_dir(folder)

app = FastAPI(
    title="Nawiri EmpowerHub API",
    description="Backend for the Nawiri EmpowerHub Website.",
    version="1.0.0"
)

# Allow frontend origin
origins = [
    "http://localhost:5173",         # For local Vite dev server
    "http://127.0.0.1:5173",   
    "https://frontend-seven-gamma-38.vercel.app",
    "https://www.nawiriempowerhub.org",
    "https://vercel.com/elvis-marubes-projects/nawiri-empowerhub/3AFd7Zd9pqYP2BmMKW4SnRzTzLYZ"
    # Alternative localhost IP
    # Add other origins if deploying
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
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