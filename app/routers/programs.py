from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, services, dependencies

router = APIRouter(tags=["Programs"])

@router.get("/api/programs", response_model=List[schemas.Program])
def read_programs(skip: int = 0, limit: int = 100, db: Session = Depends(dependencies.get_db)):
    programs = services.crud_service.get_items(db, model=models.Program, skip=skip, limit=limit)
    return programs

@router.post("/api/programs", response_model=schemas.Program, status_code=201)
def create_program(program: schemas.ProgramCreate, db: Session = Depends(dependencies.get_db), current_user: models.User = Depends(dependencies.get_current_active_user)):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to create programs")
    return services.crud_service.create_item(db=db, model=models.Program, item=program)

# ... Add endpoints for GET by ID, PUT, DELETE, etc. following this pattern ...