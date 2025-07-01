import os
import shutil
from typing import Annotated, List
from datetime import datetime
from fastapi import (
    APIRouter, Depends, HTTPException, Response, UploadFile, File, Form
)
from sqlalchemy.orm import Session
from app import models, schemas, dependencies
from app.services import crud_service
from app.utils.slugify import slugify  # You need to implement or install this

router = APIRouter(tags=["Programs"])

 # Save uploaded photo in static/media/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # go up one level from routers
static_folder = os.path.join(BASE_DIR, "static", "programs")

# ----------------------
# Create Program (with image upload)
# ----------------------
@router.post("/programs", response_model=schemas.ProgramBase, status_code=201)
def create_program(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    objectives: Annotated[List[str], Form()] = [],
    target_group: Annotated[List[str], Form()] = [],
    start_date: str = Form(None),
    end_date: str = Form(None),
    status: str = Form("Ongoing"),
    image: UploadFile = File(...),
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to create programs")

    filename = f"{datetime.utcnow().timestamp()}_{image.filename}"
    image_path = os.path.join(static_folder, filename)

    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_url = f"/{image_path}"

    slug = slugify(title)
    
    # if isinstance(objectives, str):
    #     objectives = parse_list_input(objectives)
    # if isinstance(target_group, str):
    #     target_group = parse_list_input(target_group)

    program_data = {
        "title": title,
        "slug": slug,
        "description": description,
        "category": category,
        "objectives": objectives,
        "target_group": target_group,
        "start_date": start_date,
        "end_date": end_date,
        "status": status,
        "featured_image_url": image_url,
    }

    return crud_service.create_item(db=db, model=models.Program, item=program_data)

# ----------------------
# Get All Programs
# ----------------------
@router.get("/programs", response_model=List[schemas.Program])
def read_programs(skip: int = 0, limit: int = 100, db: Session = Depends(dependencies.get_db)):
    return crud_service.get_items(db, model=models.Program, skip=skip, limit=limit)

# ----------------------
# Get Program by ID
# ----------------------
@router.get("/programs/{program_id}", response_model=schemas.Program)
def read_program(program_id: int, db: Session = Depends(dependencies.get_db)):
    program = crud_service.get_item(db, model=models.Program, item_id=program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program

# ----------------------
# Update Program by ID
# ----------------------
@router.put("/programs/{program_id}", response_model=schemas.Program)
def update_program(
    program_id: int,
    updated_program: schemas.ProgramUpdate,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to update programs")

    existing = crud_service.get_item(db, model=models.Program, item_id=program_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Program not found")

    update_data = updated_program.dict(exclude_unset=True)
    if "title" in update_data:
        update_data["slug"] = slugify(update_data["title"])

    return crud_service.update_item(db, model=models.Program, item_id=program_id, update_data=update_data)

# ----------------------
# Delete Program by ID
# ----------------------
@router.delete("/programs/{program_id}", status_code=204)
def delete_program(
    program_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete programs")

    program = db.query(models.Program).filter(models.Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail=f"Program with id {program_id} not found")

    if program.featured_image_url:
        try:
            filename = os.path.basename(program.featured_image_url)
            image_path = os.path.join(static_folder, filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Warning: Failed to delete program image: {e}")

    db.delete(program)
    db.commit()
    return Response(status_code=204)
