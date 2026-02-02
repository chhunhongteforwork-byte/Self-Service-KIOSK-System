import base64
import hmac
import hashlib
import json
from datetime import datetime, timezone
import requests

# CONSTANTS (Should ideally be in settings.py)
PAYWAY_BASE = "https://checkout-sandbox.payway.com.kh"
MERCHANT_ID = "ec463405"
API_KEY = "bd58ff19a2376a80e958e4bb7bec941db9280d6e"  # HMAC secret key
CALLBACK_URL = "https://webhook.site/be432763-57dc-4afe-8b87-64ad9983fbcd" # TODO: Change to real callback

def utc_req_time() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

def b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")

def hmac_sha512_b64(message: str, key: str) -> str:
    digest = hmac.new(key.encode("utf-8"), message.encode("utf-8"), hashlib.sha512).digest()
    return base64.b64encode(digest).decode("utf-8")

def null_to_empty(x) -> str:
    return "" if x is None else str(x)

def format_amount(amount: float, currency: str) -> str:
    """
    - USD typically: 2 decimals
    - KHR typically: integer
    """
    currency = currency.upper()
    if currency == "USD":
        return f"{amount:.2f}"
    # KHR
    return str(int(round(amount)))

def build_items_b64(items: list[dict]) -> str:
    return b64(json.dumps(items, ensure_ascii=False))

def build_generate_qr_hash(payload: dict) -> str:
    fields_in_order = [
        "req_time","merchant_id","tran_id","amount","items","first_name","last_name","email","phone",
        "purchase_type","payment_option","callback_url","return_deeplink","currency","custom_fields",
        "return_params","payout","lifetime","qr_image_template"
    ]
    raw = "".join(null_to_empty(payload.get(k)) for k in fields_in_order)
    return hmac_sha512_b64(raw, API_KEY)

def build_check_txn_hash(req_time: str, merchant_id: str, tran_id: str) -> str:
    raw = f"{req_time}{merchant_id}{tran_id}"
    return hmac_sha512_b64(raw, API_KEY)

def generate_qr(*, amount: float, currency: str, payment_option: str, tran_id: str) -> dict:
    req_time = utc_req_time()

    currency = currency.upper()
    payment_option = payment_option.lower()

    if payment_option in ("wechat", "alipay") and currency != "USD":
        raise ValueError("wechat/alipay requires USD currency")

    if currency == "KHR" and amount < 100:
        raise ValueError("Minimum amount for KHR is 100")
    if currency == "USD" and amount < 0.01:
        raise ValueError("Minimum amount for USD is 0.01")

    amount_str = format_amount(amount, currency)

    items_b64 = build_items_b64([
        {"name": "Order Payment", "quantity": 1, "price": float(amount_str)}
    ])

    payload = {
        "req_time": req_time,
        "merchant_id": MERCHANT_ID,
        "tran_id": tran_id,
        "first_name": "Walk-in",
        "last_name": "Customer",
        "email": None,
        "phone": None,
        "amount": amount_str,
        "purchase_type": "purchase",
        "payment_option": payment_option,
        "items": items_b64,
        "currency": currency,
        "callback_url": b64(CALLBACK_URL),
        "return_deeplink": None,
        "custom_fields": None,
        "return_params": None,
        "payout": None,
        "lifetime": 30,
        "qr_image_template": "template4_color",
    }

    payload["hash"] = build_generate_qr_hash(payload)

    url = f"{PAYWAY_BASE}/api/payment-gateway/v1/payments/generate-qr"
    r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

def check_transaction(tran_id: str) -> dict:
    req_time = utc_req_time()
    payload = {
        "req_time": req_time,
        "merchant_id": MERCHANT_ID,
        "tran_id": tran_id,
        "hash": build_check_txn_hash(req_time, MERCHANT_ID, tran_id),
    }

    url = f"{PAYWAY_BASE}/api/payment-gateway/v1/payments/check-transaction-2"
    r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()
