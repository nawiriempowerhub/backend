import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app import models, schemas, services
from app.dependencies import get_db, get_current_active_user

router = APIRouter(
    prefix="/api/media",
    tags=["Media"],
)

@router.get("", response_model=List[schemas.Media])
def read_all_media(
    type: schemas.MediaType = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Retrieve all media items, with an optional filter by type. Public endpoint.
    """
    query = db.query(models.Media)
    if type:
        query = query.filter(models.Media.type == type)
    media_items = query.offset(skip).limit(limit).all()
    return media_items

@router.post("", response_model=schemas.Media, status_code=status.HTTP_201_CREATED)
def create_media_item(
    media: schemas.MediaCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new media item record. Requires admin privileges.
    Note: This endpoint handles metadata. A separate mechanism is needed for file uploads.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to upload media")
    return services.crud_service.create_item(db=db, model=models.Media, item=media)

@router.get("/by-program/{program_id}", response_model=List[schemas.Media])
def read_media_by_program(
    program_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all media items linked to a specific program by program_id.
    """
    media_items = (
        db.query(models.Media)
        .filter(models.Media.program_id == program_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return media_items


@router.get("/{media_id}/program", response_model=schemas.Program)
def get_program_for_media(media_id: int, db: Session = Depends(get_db)):
    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return media.program


@router.get("/{media_id}", response_model=schemas.Media)
def get_media_by_id(media_id: int, db: Session = Depends(get_db)):
    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return media

@router.patch("/{media_id}/program", response_model=schemas.Media)
def update_media_program(
    media_id: int,
    program_update: schemas.MediaProgramUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update media")

    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Optional: Check if the new program_id exists before assigning
    if program_update.program_id is not None:
        program = db.query(models.Program).filter(models.Program.id == program_update.program_id).first()
        if not program:
            raise HTTPException(status_code=400, detail="Program not found")

    media.program_id = program_update.program_id
    db.commit()
    db.refresh(media)
    return media

@router.patch("/{media_id}", response_model=schemas.Media)
def update_media(
    media_id: int,
    media_update: schemas.MediaUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update media")

    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    update_data = media_update.dict(exclude_unset=True)

    # Optionally validate program_id if it's being updated
    if "program_id" in update_data:
        program = db.query(models.Program).filter(models.Program.id == update_data["program_id"]).first()
        if not program:
            raise HTTPException(status_code=400, detail="Program not found")

    for key, value in update_data.items():
        setattr(media, key, value)

    db.commit()
    db.refresh(media)
    return media

@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media_item(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a media item record and its associated file. Requires admin privileges.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete media")

    # Fetch media record manually to get the image filename
    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media item not found")

    # ✅ Attempt to delete the file from disk
    if media.file_url:
        try:
            filename = os.path.basename(media.file_url)
            file_path = os.path.join("static/media", filename)
            if os.path.exists(file_path):
                print(f"Deleting media file: {file_path}")
                os.remove(file_path)
        except Exception as e:
            print(f"Warning: Failed to delete media file: {e}")

    # Delete the database record
    db.delete(media)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
