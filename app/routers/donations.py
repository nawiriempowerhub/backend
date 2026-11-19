# app/routers/donations.py
"""
Donation endpoints — initiates M-Pesa STK Push via PayHero,
handles callbacks, and provides admin views.
"""

import uuid
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_db, get_current_active_user
from app.services.payhero_service import initiate_stk_push, check_transaction_status

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/donations",
    tags=["Donations"],
)


# ─── Initiate a Donation (STK Push) ──────────────────────────────────────────
@router.post("", response_model=schemas.Donation, status_code=201)
def create_donation(
    donation: schemas.DonationCreate,
    db: Session = Depends(get_db),
):
    """
    Create a donation record and trigger an M-Pesa STK Push via PayHero.
    The user will receive a push notification on their phone to enter their PIN.
    """
    # Generate a unique reference for this transaction
    external_ref = f"DON-{uuid.uuid4().hex[:10].upper()}"

    # Save the donation in PENDING state first
    new_donation = models.Donation(
        donor_name=donation.donor_name,
        email=donation.email,
        donor_phone=donation.donor_phone,
        amount=donation.amount,
        message=donation.message,
        external_reference=external_ref,
        payment_status=models.PaymentStatus.PENDING,
        payment_provider="m-pesa",
    )
    db.add(new_donation)
    db.commit()
    db.refresh(new_donation)

    # Trigger PayHero STK Push
    try:
        payhero_response = initiate_stk_push(
            phone_number=donation.donor_phone,
            amount=donation.amount,
            external_reference=external_ref,
        )

        # Update with PayHero reference if returned
        if isinstance(payhero_response, dict):
            new_donation.payhero_reference = payhero_response.get("reference")
            new_donation.payment_status = models.PaymentStatus.QUEUED
            db.commit()
            db.refresh(new_donation)

    except HTTPException:
        # STK Push failed — mark donation as failed
        new_donation.payment_status = models.PaymentStatus.FAILED
        db.commit()
        db.refresh(new_donation)
        raise

    return new_donation


# ─── PayHero Callback (Webhook) ──────────────────────────────────────────────
@router.post("/callback", status_code=200)
async def payhero_callback(
    payload: schemas.PayHeroCallbackPayload,
    db: Session = Depends(get_db),
):
    """
    Webhook endpoint called by PayHero when a transaction completes or fails.
    Must be publicly accessible (set PAYHERO_CALLBACK_URL to this endpoint).
    """
    logger.info(
        "PayHero callback received: ref=%s status=%s success=%s",
        payload.external_reference, payload.status, payload.success,
    )

    # Look up the donation by external reference
    donation = (
        db.query(models.Donation)
        .filter(models.Donation.external_reference == payload.external_reference)
        .first()
    )

    if not donation:
        logger.warning(
            "Callback for unknown reference: %s", payload.external_reference
        )
        return {"ResultCode": 0, "ResultDesc": "Accepted (unknown reference)"}

    # Update the donation record
    if payload.success and payload.status and payload.status.lower() == "success":
        donation.payment_status = models.PaymentStatus.SUCCESS
    else:
        donation.payment_status = models.PaymentStatus.FAILED

    donation.payhero_reference = payload.reference
    donation.provider_reference = payload.provider_reference

    if payload.transaction_date:
        try:
            donation.transaction_date = datetime.fromisoformat(
                payload.transaction_date.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            pass

    db.commit()

    logger.info(
        "Donation #%d updated → %s (M-Pesa receipt: %s)",
        donation.id, donation.payment_status.value,
        donation.provider_reference or "N/A",
    )

    return {"ResultCode": 0, "ResultDesc": "Accepted"}


# ─── Check Transaction Status (manual polling) ──────────────────────────────
@router.get("/status/{external_reference}")
def get_donation_status(
    external_reference: str,
    db: Session = Depends(get_db),
):
    """
    Check the payment status of a donation.
    First checks the local DB; if still PENDING/QUEUED, queries PayHero directly.
    """
    donation = (
        db.query(models.Donation)
        .filter(models.Donation.external_reference == external_reference)
        .first()
    )

    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")

    # If still pending, try to get a fresh status from PayHero
    if donation.payment_status in (
        models.PaymentStatus.PENDING,
        models.PaymentStatus.QUEUED,
    ):
        try:
            ph_status = check_transaction_status(external_reference)
            status_str = ph_status.get("status", "").upper()

            if status_str == "SUCCESS":
                donation.payment_status = models.PaymentStatus.SUCCESS
                donation.provider_reference = ph_status.get("payment_reference")
            elif status_str == "FAILED":
                donation.payment_status = models.PaymentStatus.FAILED

            db.commit()
            db.refresh(donation)
        except HTTPException:
            pass  # Return the last known local status

    return {
        "id": donation.id,
        "external_reference": donation.external_reference,
        "amount": donation.amount,
        "payment_status": donation.payment_status.value,
        "provider_reference": donation.provider_reference,
        "created_at": donation.created_at,
    }


# ─── Admin: List All Donations ───────────────────────────────────────────────
@router.get("", response_model=List[schemas.Donation])
def get_all_donations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """List all donations (admin only)."""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admins only")
    return (
        db.query(models.Donation)
        .order_by(models.Donation.created_at.desc())
        .all()
    )


# ─── Admin: Get Single Donation ──────────────────────────────────────────────
@router.get("/{donation_id}", response_model=schemas.Donation)
def get_donation_by_id(
    donation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get a single donation by ID (admin only)."""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admins only")

    donation = (
        db.query(models.Donation)
        .filter(models.Donation.id == donation_id)
        .first()
    )
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation
