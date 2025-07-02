# # app/routers/stk_push.py
# import requests, base64
# from datetime import datetime
# from fastapi import APIRouter
# from pydantic import BaseModel
# from dotenv import load_dotenv
# import os

# load_dotenv()

# router = APIRouter()

# # ENV variables
# consumer_key = os.getenv("MPESA_CONSUMER_KEY")
# consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
# shortcode = os.getenv("MPESA_SHORTCODE", "174379")
# passkey = os.getenv("MPESA_PASSKEY")
# callback_url = os.getenv("MPESA_CALLBACK_URL")

# class STKPushRequest(BaseModel):
#     amount: int
#     donor_phone: str

# def get_access_token():
#     response = requests.get(
#         "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
#         auth=(consumer_key, consumer_secret)
#     )
#     return response.json()["access_token"]

# @router.post("/stk_push")
# def stk_push(data: STKPushRequest):
#     access_token = get_access_token()
#     timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#     password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode()

#     payload = {
#         "BusinessShortCode": shortcode,
#         "Password": password,
#         "Timestamp": timestamp,
#         "TransactionType": "CustomerPayBillOnline",
#         "Amount": data.amount,
#         "PartyA": data.donor_phone,
#         "PartyB": shortcode,
#         "PhoneNumber": data.donor_phone,
#         "CallBackURL": callback_url,
#         "AccountReference": "7964728",
#         "TransactionDesc": "Donation"
#     }

#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json",
#     }

#     res = requests.post(
#         "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
#         json=payload,
#         headers=headers
#     )
#     return res.json()
