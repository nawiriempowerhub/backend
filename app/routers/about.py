from datetime import date
import os
import shutil
from uuid import uuid4
from fastapi import APIRouter, Depends, Form, HTTPException, File, Request, UploadFile
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/about", tags=["About"])


@router.post("/", response_model=schemas.About)
def create_about(
    data: schemas.AboutCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    about = models.About(**data.dict())
    db.add(about)
    db.commit()
    db.refresh(about)
    return about


@router.get("/", response_model=schemas.About)
def get_about(db: Session = Depends(get_db)):
    about = db.query(models.About).first()
    if not about:
        raise HTTPException(status_code=404, detail="About info not found")
    return about


@router.put("/", response_model=schemas.About)
def update_about(
    data: schemas.AboutUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    about = db.query(models.About).first()
    if not about:
        raise HTTPException(status_code=404, detail="About info not found")
    for key, value in data.dict().items():
        setattr(about, key, value)
    db.commit()
    db.refresh(about)
    return about


@router.post("/team", response_model=schemas.TeamMember)
def add_team_member(
    name: str,
    role: str,
    bio: str,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Save uploaded photo in static/team/
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # go up one level from routers
    static_folder = os.path.join(BASE_DIR, "static", "team")
    os.makedirs(static_folder, exist_ok=True)

    filename = f"{uuid4().hex}_{photo.filename}"
    filepath = os.path.join(static_folder, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)

    # Save only filename in DB
    member = models.TeamMember(
        name=name,
        role=role,
        bio=bio,
        photo_filename=filename,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get("/team", response_model=List[schemas.TeamMember])
def get_team_members(db: Session = Depends(get_db)):
    members = db.query(models.TeamMember).all()
    return members  # Just return the DB model, Pydantic will serialize


@router.put("/team/{member_id}", response_model=schemas.TeamMember)
def update_team_member(
    member_id: int,
    name: str = None,
    role: str = None,
    bio: str = None,
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    member = (
        db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")

    if name:
        member.name = name
    if role:
        member.role = role
    if bio:
        member.bio = bio
    if photo:
        BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # go up one level from routers
        static_folder = os.path.join(BASE_DIR, "static", "team")
        os.makedirs(static_folder, exist_ok=True)
        filename = f"{uuid4().hex}_{photo.filename}"
        filepath = os.path.join(static_folder, filename)
        print(f"Saving to: {filepath}")

 
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        member.photo_filename = filename

    db.commit()
    db.refresh(member)
    return member


@router.delete("/team/{member_id}")
def delete_team_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    member = db.query(models.TeamMember).filter(models.TeamMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")

    # ✅ Delete image file from disk if exists
    if member.photo_filename:
        try:
            filename = os.path.basename(member.photo_filename)
            image_path = os.path.join(os.path.dirname(__file__), "static", "team", filename)
            if os.path.exists(image_path):
                print(f"Deleting team member photo file: {image_path}")
                os.remove(image_path)
        except Exception as e:
            print(f"Warning: failed to delete team member photo file: {e}")

    db.delete(member)
    db.commit()
    return {"detail": "Team member deleted successfully"}



@router.post("/impact", response_model=schemas.ImpactEvent)
def add_impact_event(
    title: str = Form(...),
    description: str = Form(...),
    date: date = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    request: Request = None,
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Save image
    static_folder = "static/impact"
    os.makedirs(static_folder, exist_ok=True)
    filename = f"{uuid4().hex}_{image.filename}"
    filepath = os.path.join(static_folder, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # ✅ Generate full image URL
    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/static/impact/{filename}"  # This is now a full URL

    # ✅ Save full URL to DB
    db_event = models.ImpactEvent(
        title=title, description=description, date=date, image_filename=image_url
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event


@router.get("/impact", response_model=List[schemas.ImpactEvent])
def get_impact_events(request: Request, db: Session = Depends(get_db)):
    impact_events = db.query(models.ImpactEvent).all()
    base_url = request.base_url
    for event in impact_events:
        event.image_filename = str(base_url) + f"static/impact/{event.image_filename}"
    return impact_events


@router.put("/impact/{impact_id}", response_model=schemas.ImpactEvent)
def update_impact_event(
    impact_id: int,
    title: str = None,
    description: str = None,
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    request: Request = None  # ✅ Inject FastAPI request to build full image URL
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    event = db.query(models.ImpactEvent).filter(models.ImpactEvent.id == impact_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Impact event not found")

    if title:
        event.title = title
    if description:
        event.description = description
    if image:
        static_folder = "static/impact"
        os.makedirs(static_folder, exist_ok=True)
        filename = f"{uuid4().hex}_{image.filename}"
        filepath = os.path.join(static_folder, filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # ✅ Generate full image URL for schema validation
        base_url = str(request.base_url).rstrip("/")
        event.image_filename = f"{base_url}/static/impact/{filename}"

    db.commit()
    db.refresh(event)
    return event

@router.delete("/impact/{impact_id}")
def delete_impact_event(
    impact_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    event = db.query(models.ImpactEvent).filter(models.ImpactEvent.id == impact_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Impact event not found")

    # ✅ Delete image file from disk if exists
    if event.image_filename:
        try:
            # Extract actual filename from full URL
            filename = os.path.basename(event.image_filename)
            image_path = os.path.join("static/impact", filename)
            if os.path.exists(image_path):
                print(f"Deleting image file: {image_path}")
                os.remove(image_path)
        except Exception as e:
            print(f"Warning: failed to delete image file: {e}")

    db.delete(event)
    db.commit()
    return {"detail": "Impact event deleted successfully"}
