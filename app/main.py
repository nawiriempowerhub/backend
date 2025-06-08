from fastapi import FastAPI

from app.routers import about
from .database import engine, Base
from .routers import auth, programs, media, contact, volunteers, events
from fastapi.staticfiles import StaticFiles
import os

# Create database tables
Base.metadata.create_all(bind=engine)

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

app = FastAPI(
    title="Nawiri EmpowerHub API",
    description="Backend for the Nawiri EmpowerHub Website.",
    version="1.0.0"
)

# Include all the routers
app.include_router(auth.router)
app.include_router(programs.router)
app.include_router(media.router)
app.include_router(contact.router)
app.include_router(volunteers.router)
app.include_router(events.router)
app.include_router(about.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Nawiri EmpowerHub API"}

app.mount("/static", StaticFiles(directory="static"), name="static")