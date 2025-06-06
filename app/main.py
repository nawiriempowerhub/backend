from fastapi import FastAPI
from .database import engine, Base
from .routers import auth, programs, blogs, media, contact, volunteers, events

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Nawiri EmpowerHub API",
    description="Backend for the Nawiri EmpowerHub Website.",
    version="1.0.0"
)

# Include all the routers
app.include_router(auth.router)
app.include_router(programs.router)
app.include_router(blogs.router)
app.include_router(media.router)
app.include_router(contact.router)
app.include_router(volunteers.router)
app.include_router(events.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Nawiri EmpowerHub API"}