# app/services/payhero_service.py
"""
PayHero API v2 integration service.
Handles M-Pesa STK Push payments via PayHero's gateway.
Docs: https://payhero.co.ke
"""

import base64
import logging
import requests
from typing import Optional

from fastapi import HTTPException
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
PAYHERO_BASE_URL = os.getenv("PAYHERO_BASE_URL", "https://backend.payhero.co.ke")
PAYHERO_BASIC_AUTH_TOKEN = os.getenv("PAYHERO_BASIC_AUTH_TOKEN", "")
PAYHERO_API_USERNAME = os.getenv("PAYHERO_API_USERNAME", "")
PAYHERO_API_PASSWORD = os.getenv("PAYHERO_API_PASSWORD", "")
try:
    PAYHERO_CHANNEL_ID = int(os.getenv("PAYHERO_CHANNEL_ID", "0"))
except ValueError:
    PAYHERO_CHANNEL_ID = 0
    logger.warning("PAYHERO_CHANNEL_ID is not a valid integer — set it in your .env")
PAYHERO_CALLBACK_URL = os.getenv("PAYHERO_CALLBACK_URL", "")


def _get_auth_header() -> str:
    """Build the HTTP Basic Auth header value."""
    # 1. Direct Basic Auth Token (from PayHero dashboard)
    if PAYHERO_BASIC_AUTH_TOKEN:
        token = PAYHERO_BASIC_AUTH_TOKEN.strip()
        return token if token.startswith("Basic ") else f"Basic {token}"

    # 2. Base64 encode username:password
    if not PAYHERO_API_USERNAME or not PAYHERO_API_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="PayHero API credentials are not configured"
        )
    credentials = f"{PAYHERO_API_USERNAME}:{PAYHERO_API_PASSWORD}"
    encoded = base64.b64encode(credentials.encode()).decode("utf-8")
    return f"Basic {encoded}"


def _headers() -> dict:
    return {
        "Authorization": _get_auth_header(),
        "Content-Type": "application/json",
    }


# ─── Initiate STK Push ───────────────────────────────────────────────────────
def initiate_stk_push(
    phone_number: str,
    amount: float,
    external_reference: str,
    callback_url: Optional[str] = None,
) -> dict:
    """
    Trigger an M-Pesa STK Push via PayHero.

    Args:
        phone_number: Customer's phone number (07XXXXXXXX / 2547XXXXXXXX).
        amount: Amount in KES.
        external_reference: Your internal tracking/invoice reference.
        callback_url: Override the default callback URL (optional).

    Returns:
        PayHero API response dict.

    Raises:
        HTTPException: On API failure.
    """
    url = f"{PAYHERO_BASE_URL}/api/v2/payments"

    # Clean phone number (strip '+', spaces, hyphens)
    cleaned_phone = str(phone_number).replace("+", "").replace(" ", "").replace("-", "").strip()

    payload = {
        "amount": amount,
        "phone_number": cleaned_phone,
        "channel_id": PAYHERO_CHANNEL_ID,
        "provider": "m-pesa",
        "external_reference": external_reference,
        "callback_url": callback_url or PAYHERO_CALLBACK_URL,
    }

    logger.info(
        "Initiating PayHero STK Push: phone=%s amount=%s ref=%s",
        phone_number, amount, external_reference,
    )

    try:
        response = requests.post(url, headers=_headers(), json=payload, timeout=30)
    except requests.exceptions.RequestException as exc:
        logger.error("PayHero request failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"PayHero gateway error: {exc}")

    if response.status_code not in (200, 201):
        logger.error(
            "PayHero STK Push failed [%s]: %s",
            response.status_code, response.text,
        )
        raise HTTPException(
            status_code=502,
            detail=f"PayHero STK Push failed: {response.text}",
        )

    data = response.json()
    logger.info("PayHero STK Push accepted: %s", data)
    return data


# ─── Check Transaction Status ────────────────────────────────────────────────
def check_transaction_status(reference: str) -> dict:
    """
    Query the status of a PayHero transaction.

    Args:
        reference: The external_reference or PayHero reference.

    Returns:
        PayHero transaction status dict.
    """
    url = f"{PAYHERO_BASE_URL}/api/v2/transaction-status"

    try:
        response = requests.get(
            url,
            headers=_headers(),
            params={"reference": reference},
            timeout=30,
        )
    except requests.exceptions.RequestException as exc:
        logger.error("PayHero status check failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"PayHero gateway error: {exc}")

    if response.status_code != 200:
        logger.error(
            "PayHero status check failed [%s]: %s",
            response.status_code, response.text,
        )
        raise HTTPException(
            status_code=502,
            detail=f"PayHero status check failed: {response.text}",
        )

    return response.json()
