# api/donations.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.dependencies import get_db, get_current_active_user

router = APIRouter(
    prefix="/api/donations",
    tags=["Donations"]
)

@router.post("", response_model=schemas.Donation, status_code=201)
def create_donation(
    donation: schemas.DonationCreate,
    db: Session = Depends(get_db)
):
    new_donation = models.Donation(**donation.dict())
    db.add(new_donation)
    db.commit()
    db.refresh(new_donation)
    return new_donation

@router.get("", response_model=List[schemas.Donation])
def get_all_donations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admins only")
    return db.query(models.Donation).order_by(models.Donation.created_at.desc()).all()

@router.get("/{donation_id}", response_model=schemas.Donation)
def get_donation_by_id(
    donation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admins only")

    donation = db.query(models.Donation).filter(models.Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation
