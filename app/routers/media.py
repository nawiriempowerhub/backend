import os
import shutil
from typing import List, Optional
from fastapi import (
    APIRouter, Depends, HTTPException, Response, status, UploadFile, File, Form
)
from sqlalchemy.orm import Session
from app import models, schemas
from app.dependencies import get_db, get_current_active_user
from app.utils.storage import save_upload_file, delete_file
from datetime import datetime

router = APIRouter(
    prefix="/media",
    tags=["Media"],
)

# 1. Get all media with optional type filter
@router.get("", response_model=List[schemas.Media])
def read_all_media(
    type: Optional[schemas.MediaType] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.Media)
    if type:
        query = query.filter(models.Media.type == type)
    return query.offset(skip).limit(limit).all()


# 2. Upload Media (File + Metadata via Multipart Form)
@router.post("", response_model=schemas.Media, status_code=status.HTTP_201_CREATED)
def create_media_item(
    title: str = Form(...),
    type: schemas.MediaType = Form(...),
    description: Optional[str] = Form(None),
    program_id: Optional[int] = Form(None),
    external_link: Optional[str] = Form(None),
    is_featured: Optional[bool] = Form(False),
    file_url: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to upload media")

    saved_file_url = None
    if file_url:
        saved_file_url = save_upload_file(file_url, "media")

    media = models.Media(
        title=title,
        type=type,
        description=description,
        program_id=program_id,
        external_link=external_link,
        is_featured=is_featured,
        file_url=saved_file_url,
        created_at=datetime.utcnow(),
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


# 2b. Batch Upload Media (Multiple files for a specific program)
@router.post("/batch", response_model=List[schemas.Media], status_code=status.HTTP_201_CREATED)
def create_batch_media(
    program_id: Optional[int] = Form(None),
    title_prefix: Optional[str] = Form(None),
    type: schemas.MediaType = Form(schemas.MediaType.PHOTO),
    description: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to upload media")

    created_items = []

    # Infer title prefix from program if not provided
    if not title_prefix and program_id:
        prog = db.query(models.Program).filter(models.Program.id == program_id).first()
        if prog:
            title_prefix = prog.title

    base_title = title_prefix or "Media Item"

    for idx, upload_file in enumerate(files, 1):
        if not upload_file or not upload_file.filename:
            continue

        saved_url = save_upload_file(upload_file, "media")
        item_title = f"{base_title} #{idx}" if len(files) > 1 else base_title

        media_item = models.Media(
            title=item_title,
            type=type,
            description=description,
            program_id=program_id,
            file_url=saved_url,
            created_at=datetime.utcnow(),
        )
        db.add(media_item)
        created_items.append(media_item)

    db.commit()
    for item in created_items:
        db.refresh(item)

    return created_items


# 3. Get media by program
@router.get("/by-program/{program_id}", response_model=List[schemas.Media])
def read_media_by_program(
    program_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return db.query(models.Media).filter(models.Media.program_id == program_id).offset(skip).limit(limit).all()


# 4. Get program for media
@router.get("/{media_id}/program", response_model=schemas.Program)
def get_program_for_media(media_id: int, db: Session = Depends(get_db)):
    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return media.program


# 5. Get single media item
@router.get("/{media_id}", response_model=schemas.Media)
def get_media_by_id(media_id: int, db: Session = Depends(get_db)):
    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return media


# 6. Update program_id of media
@router.patch("/{media_id}/program", response_model=schemas.Media)
def update_media_program(
    media_id: int,
    program_update: schemas.MediaProgramUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to update media")

    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

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
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    type: Optional[schemas.MediaType] = Form(None),
    program_id: Optional[int] = Form(None),
    external_link: Optional[str] = Form(None),
    is_featured: Optional[bool] = Form(None),
    tags: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to update media")

    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    if program_id is not None:
        program = db.query(models.Program).filter(models.Program.id == program_id).first()
        if not program:
            raise HTTPException(status_code=400, detail="Program not found")

    # Handle file upload
    if file:
        if media.file_url:
            delete_file(media.file_url, "media")
        media.file_url = save_upload_file(file, "media")

    # Update fields if provided
    if title is not None: media.title = title
    if description is not None: media.description = description
    if type is not None: media.type = type
    if external_link is not None: media.external_link = external_link
    if is_featured is not None: media.is_featured = is_featured
    if tags is not None: media.tags = tags
    if program_id is not None: media.program_id = program_id

    db.commit()
    db.refresh(media)
    return media


# 8. Delete media and remove associated file
@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media_item(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete media")

    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media item not found")

    if media.file_url:
        delete_file(media.file_url, "media")

    db.delete(media)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
