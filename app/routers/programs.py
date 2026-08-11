import os
import shutil
import json
from typing import Annotated, List
from datetime import datetime
from fastapi import (
    APIRouter, Depends, HTTPException, Response, UploadFile, File, Form
)
from sqlalchemy.orm import Session
from app import models, schemas, dependencies
from app.services import crud_service
from app.utils.slugify import slugify  # You need to implement or install this

from app.utils.storage import save_upload_file, delete_file

router = APIRouter(tags=["Programs"])

# Helper function to parse the stringified list
def parse_list_input(input_string: str) -> List[str]:
    try:
        parsed = json.loads(input_string)
        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
            return parsed
    except json.JSONDecodeError:
        pass

    # Fallback: try comma-separated
    return [item.strip() for item in input_string.split(",") if item.strip()]

# ----------------------
# Create Program (with image upload)
# ----------------------
@router.post("/programs", response_model=schemas.ProgramBase, status_code=201)
def create_program(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    impact: str = Form("[]"),  # Expect a stringified JSON array
    reason: str = Form("[]"),  # Expect a stringified JSON array
    key_activities: str = Form("[]"),  # Expect a stringified JSON array
    invitations: str = Form(None),  # Optional string for invitations
    objectives: str = Form("[]"), # Expect a string, default to empty JSON array string
    status: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to create programs")

    image_url = save_upload_file(image, "programs")

    # Parse objectives and target_group from stringified JSON
    parsed_objectives = parse_list_input(objectives)
    parsed_impact = parse_list_input(impact)
    parsed_reason = parse_list_input(reason)
    parsed_key_activities = parse_list_input(key_activities)

    program_data = {
        "title": title,
        "description": description,
        "category": category,
        "objectives": parsed_objectives,
        "reason": parsed_reason,
        "key_activities": parsed_key_activities,
        "invitations": invitations,
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
        delete_file(program.featured_image_url, "programs")

    db.delete(program)
    db.commit()
    return Response(status_code=204)
