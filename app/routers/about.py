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


@router.post("", response_model=schemas.About)
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


@router.get("", response_model=schemas.About)
def get_about(db: Session = Depends(get_db)):
    about = db.query(models.About).first()
    if not about:
        raise HTTPException(status_code=404, detail="About info not found")
    return about


@router.put("", response_model=schemas.About)
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


from app.utils.storage import save_upload_file, delete_file

@router.post("/team", response_model=schemas.TeamMember)
def add_team_member(
    name: str,
    role: str,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    photo_url = save_upload_file(photo, "team")
    member = models.TeamMember(
        name=name,
        role=role,
        photo_filename=photo_url,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

@router.get("/team", response_model=List[schemas.TeamMember])
def get_team_members(db: Session = Depends(get_db)):
    members = db.query(models.TeamMember).all()
    return members


@router.put("/team/{member_id}", response_model=schemas.TeamMember)
def update_team_member(
    member_id: int,
    name: str = None,
    role: str = None,
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
    if photo:
        if member.photo_filename:
            delete_file(member.photo_filename, "team")
        member.photo_filename = save_upload_file(photo, "team")

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

    if member.photo_filename:
        delete_file(member.photo_filename, "team")

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
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    image_url = save_upload_file(image, "impact")

    db_event = models.ImpactEvent(
        title=title, description=description, date=date, image_filename=image_url
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event


@router.get("/impact", response_model=List[schemas.ImpactEvent])
def get_impact_events(db: Session = Depends(get_db)):
    return db.query(models.ImpactEvent).all()


@router.put("/impact/{impact_id}", response_model=schemas.ImpactEvent)
def update_impact_event(
    impact_id: int,
    title: str = None,
    description: str = None,
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
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
        if event.image_filename:
            delete_file(event.image_filename, "impact")
        event.image_filename = save_upload_file(image, "impact")

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

    if event.image_filename:
        delete_file(event.image_filename, "impact")

    db.delete(event)
    db.commit()
    return {"detail": "Impact event deleted successfully"}
