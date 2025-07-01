from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

import app

router = APIRouter()

class STKCallbackData(BaseModel):
    Body: dict

@router.post("/mpesa/callback")
async def mpesa_callback(data: STKCallbackData):
    # Safaricom posts data under 'Body'
    result = data.Body.get("stkCallback", {})
    result_code = result.get("ResultCode")
    checkout_request_id = result.get("CheckoutRequestID")
    amount = result.get("CallbackMetadata", {}).get("Item", [])

    # TODO: store/update transaction in your DB
    print("STK Push callback received:", result)

    return {"ResultCode": 0, "ResultDesc": "Accepted"}
