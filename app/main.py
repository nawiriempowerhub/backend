from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware  # ✅ Correct
from dotenv import load_dotenv

from app.routers import about, donations
from .database import engine, Base
from .routers import auth, programs, media, contact, volunteers, events, stk_push, mpesa_callback
from fastapi.staticfiles import StaticFiles
import os

# Load environment variables from .env file
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

app = FastAPI(
    title="Nawiri EmpowerHub API",
    description="Backend for the Nawiri EmpowerHub Website.",
    version="1.0.0"
)

# Allow frontend origin
origins = [
    "http://localhost:5173",         # For local Vite dev server
    "http://127.0.0.1:5173",         # Alternative localhost IP
    # Add other origins if deploying
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Accept requests from these origins
    allow_credentials=True,
    allow_methods=["*"],              # Allow all HTTP methods
    allow_headers=["*"],              # Allow all headers
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
app.include_router(stk_push.router)
app.include_router(mpesa_callback.router)
# app.include_router(submission.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Nawiri EmpowerHub API"}

# Ensure path is correct relative to this file
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")