from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
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

@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media_item(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a media item record. Requires admin privileges.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete media")
    
    db_media = services.crud_service.delete_item(db, model=models.Media, item_id=media_id)
    if not db_media:
        raise HTTPException(status_code=404, detail="Media item not found")
        
    return