from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File, Form
from sqlalchemy.orm import Session
from app import models, schemas, services, dependencies
from app.services import crud_service
import shutil
import os
from datetime import datetime

router = APIRouter(tags=["Programs"])

# ----------------------
# Create Program (with image upload)
# ----------------------
@router.post("/api/programs", response_model=schemas.Program, status_code=201)
def create_program(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to create programs")

    image_filename = f"{datetime.utcnow().timestamp()}_{image.filename}"
    image_path = f"static/programs/{image_filename}"
    os.makedirs("static/programs", exist_ok=True)
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_url = f"/static/programs/{image_filename}"

    program_data = {
        "title": title,
        "description": description,
        "category": category,
        "image_url": image_url,
    }

    return crud_service.create_item(db=db, model=models.Program, item=program_data)


# ----------------------
# Get All Programs
# ----------------------
@router.get("/api/programs", response_model=List[schemas.Program])
def read_programs(skip: int = 0, limit: int = 100, db: Session = Depends(dependencies.get_db)):
    return crud_service.get_items(db, model=models.Program, skip=skip, limit=limit)


# ----------------------
# Get Program by ID
# ----------------------
@router.get("/api/programs/{program_id}", response_model=schemas.Program)
def read_program(program_id: int, db: Session = Depends(dependencies.get_db)):
    program = crud_service.get_item(db, model=models.Program, item_id=program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


# ----------------------
# Update Program by ID
# ----------------------
@router.put("/api/programs/{program_id}", response_model=schemas.Program)
def update_program(
    program_id: int,
    updated_program: schemas.ProgramUpdate,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to update programs")

    existing_program = crud_service.get_item(db, model=models.Program, item_id=program_id)
    if not existing_program:
        raise HTTPException(status_code=404, detail="Program not found")

    return crud_service.update_item(db, model=models.Program, item_id=program_id, update_data=updated_program.dict())


# ----------------------
# Delete Program by ID
# ----------------------
@router.delete("/api/programs/{program_id}", status_code=204)
def delete_program(
    program_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete programs")

    # Fetch program first to access image filename
    program = db.query(models.Program).filter(models.Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail=f"Program with id {program_id} not found")

    # ✅ Delete image file from disk if it exists
    if program.image_url:
        try:
            filename = os.path.basename(program.image_url)
            image_path = os.path.join("static/programs", filename)  # adjust folder name
            if os.path.exists(image_path):
                print("Program image_url:", program.image_url)
                print(f"Deleting program image: {image_path}")
                os.remove(image_path)
        except Exception as e:
            print(f"Warning: Failed to delete program image: {e}")

    # Delete the DB record
    db.delete(program)
    db.commit()

    return Response(status_code=204)