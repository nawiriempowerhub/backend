import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 1. Prefer direct DATABASE_URL (automatically provided by Railway, Heroku, etc.)
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Fallback to individual credentials if DATABASE_URL is not set
if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DB_DIALECT = os.getenv("DB_DIALECT", "postgresql")

    if DB_USER and DB_PASSWORD and DB_HOST and DB_NAME:
        DATABASE_URL = f"{DB_DIALECT}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        raise ValueError(
            "Database connection failed: neither DATABASE_URL nor full DB_* environment variables are set."
        )

# Normalize URL for SQLAlchemy to use psycopg2 (from psycopg2-binary)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

print("DATABASE_URL is configured successfully.")

# SQLAlchemy engine setup
engine = create_engine(DATABASE_URL)

# Session setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

def get_db():
    """Dependency to get a DB session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()