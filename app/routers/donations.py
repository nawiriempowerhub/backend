# api/donations.py
import base64
from datetime import datetime
import os
from fastapi import APIRouter, Depends, HTTPException
import requests
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

consumer_key = os.getenv("MPESA_CONSUMER_KEY")
consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
shortcode = os.getenv("MPESA_SHORTCODE", "174379")
passkey = os.getenv("MPESA_PASSKEY")
callback_url = os.getenv("MPESA_CALLBACK_URL")

def get_access_token():
    res = requests.get(
        "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
        auth=(consumer_key, consumer_secret)
    )
    if res.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to authenticate with M-Pesa")
    return res.json()["access_token"]

@router.post("/mpesa", response_model=schemas.Donation)
def create_mpesa_donation(
    donation: schemas.DonationCreate,
    db: Session = Depends(get_db)
):
    # Send STK Push
    access_token = get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode()

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": donation.amount,
        "PartyA": donation.donor_phone,
        "PartyB": shortcode,
        "PhoneNumber": donation.donor_phone,
        "CallBackURL": callback_url,
        "AccountReference": "7964728" ,
        "TransactionDesc": donation.message or "Donation"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    mpesa_res = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers=headers
    )

    if mpesa_res.status_code != 200 or mpesa_res.json().get("ResponseCode") != "0":
        raise HTTPException(
            status_code=502,
            detail="M-Pesa STK Push failed"
        )

    # Save donation to DB
    new_donation = models.Donation(**donation.dict())
    db.add(new_donation)
    db.commit()
    db.refresh(new_donation)
    return new_donation