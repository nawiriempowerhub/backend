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


# ─── Debug: Check PayHero config (remove in production) ──────────────────────
@router.get("/debug/config")
def debug_config():
    """Temporarily check if PayHero env vars are loaded. Remove after debugging."""
    from app.services.payhero_service import (
        PAYHERO_API_USERNAME, PAYHERO_API_PASSWORD,
        PAYHERO_CHANNEL_ID, PAYHERO_CALLBACK_URL, PAYHERO_BASE_URL,
    )
    return {
        "base_url": PAYHERO_BASE_URL,
        "username_set": bool(PAYHERO_API_USERNAME),
        "username_preview": PAYHERO_API_USERNAME[:5] + "..." if PAYHERO_API_USERNAME else "(empty)",
        "password_set": bool(PAYHERO_API_PASSWORD),
        "channel_id": PAYHERO_CHANNEL_ID,
        "callback_url": PAYHERO_CALLBACK_URL,
    }


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
    try:
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
    except Exception as db_err:
        db.rollback()
        logger.exception("Database error while creating donation record: %s", db_err)
        raise HTTPException(
            status_code=500,
            detail=f"Database error saving donation: {db_err}"
        )

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

    except HTTPException as exc:
        # STK Push failed — mark donation as failed and return the actual error
        new_donation.payment_status = models.PaymentStatus.FAILED
        db.commit()
        db.refresh(new_donation)
        raise HTTPException(
            status_code=exc.status_code,
            detail=f"STK Push failed: {exc.detail}"
        )

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


# ─── Helper: Find Donation by ID or Reference ────────────────────────────────
def _find_donation(db: Session, identifier: str):
    if str(identifier).isdigit():
        donation = db.query(models.Donation).filter(models.Donation.id == int(identifier)).first()
        if donation:
            return donation
    return (
        db.query(models.Donation)
        .filter(models.Donation.external_reference == identifier)
        .first()
    )


def _sync_live_status(db: Session, donation: models.Donation):
    """If still pending, query PayHero to get real-time outcome."""
    if donation.payment_status in (
        models.PaymentStatus.PENDING,
        models.PaymentStatus.QUEUED,
    ) and donation.external_reference:
        try:
            ph_status = check_transaction_status(donation.external_reference)
            status_str = ph_status.get("status", "").upper()

            if status_str == "SUCCESS":
                donation.payment_status = models.PaymentStatus.SUCCESS
                donation.provider_reference = ph_status.get("payment_reference")
            elif status_str == "FAILED":
                donation.payment_status = models.PaymentStatus.FAILED

            db.commit()
            db.refresh(donation)
        except Exception as e:
            logger.warning("Could not sync PayHero status live: %s", e)
    return donation


# ─── Check Transaction Status (by ID or external_reference) ──────────────────
@router.get("/status/{identifier}")
def get_donation_status(
    identifier: str,
    db: Session = Depends(get_db),
):
    """
    Check payment status. Accepts either numeric ID (e.g. 10) or external_reference (DON-...).
    """
    donation = _find_donation(db, identifier)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")

    donation = _sync_live_status(db, donation)

    return {
        "id": donation.id,
        "external_reference": donation.external_reference,
        "amount": donation.amount,
        "payment_status": donation.payment_status.value if donation.payment_status else "PENDING",
        "provider_reference": donation.provider_reference,
        "created_at": donation.created_at,
    }


# ─── Public / Frontend Poll by Donation ID ───────────────────────────────────
@router.get("/{donation_id}", response_model=schemas.Donation)
def get_donation_by_id(
    donation_id: str,
    db: Session = Depends(get_db),
):
    """
    Get donation status by ID (used by frontend polling).
    """
    donation = _find_donation(db, donation_id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")

    donation = _sync_live_status(db, donation)
    return donation


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
