import base64
import hmac
import hashlib
import json
from datetime import datetime, timezone

import requests
from flask import Flask, request, jsonify

# ======================
# CONFIG (DON'T COMMIT)
# ======================
PAYWAY_BASE = "https://checkout-sandbox.payway.com.kh"
MERCHANT_ID = "ec463405"
API_KEY = "bd58ff19a2376a80e958e4bb7bec941db9280d6e"  # HMAC secret key from ABA/PayWay (NOT RSA keys)

# Webhook.site URL (PayWay pushback will go here for quick testing)
CALLBACK_URL = "https://webhook.site/be432763-57dc-4afe-8b87-64ad9983fbcd"

# ======================
# HELPERS
# ======================
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
    Some gateways are picky about amount string formatting.
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

# ======================
# PAYWAY CALLS
# ======================
def generate_qr(*, amount: float, currency: str, payment_option: str, tran_id: str) -> dict:
    req_time = utc_req_time()

    currency = currency.upper()
    payment_option = payment_option.lower()

    # Guard: WeChat/Alipay usually support USD only
    if payment_option in ("wechat", "alipay") and currency != "USD":
        raise ValueError("wechat/alipay requires USD currency")

    # Guard: minimum amount (based on your earlier doc)
    # KHR >= 100, USD >= 0.01
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

        # NOTE: use string to keep hashing consistent
        "amount": amount_str,
        "purchase_type": "purchase",
        "payment_option": payment_option,
        "items": items_b64,
        "currency": currency,

        # PayWay expects Base64-encoded callback URL string
        "callback_url": b64(CALLBACK_URL),

        "return_deeplink": None,
        "custom_fields": None,
        "return_params": None,
        "payout": None,

        # Minutes (30 minutes). If you want 30 days, use 43200.
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

# ======================
# FLASK APP
# ======================
app = Flask(__name__)

@app.get("/")
def home():
    return "PayWay test server running ✅", 200

@app.get("/pos")
def pos_page():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>PayWay POS QR</title>
  <style>
    body{font-family:Arial, sans-serif; margin:0; background:#fafafa; color:#111;}
    .wrap{max-width:520px; margin:0 auto; padding:24px;}
    .card{background:#fff; border:1px solid #e8e8e8; border-radius:16px; padding:18px; box-shadow:0 2px 10px rgba(0,0,0,.04);}
    h1{font-size:20px; margin:0 0 12px;}
    .row{display:flex; gap:10px; flex-wrap:wrap; align-items:center;}
    label{font-size:13px; color:#444;}
    input, select{padding:10px 12px; border:1px solid #ddd; border-radius:10px; font-size:16px;}
    button{padding:10px 14px; border:0; border-radius:10px; background:#111; color:#fff; font-size:16px; cursor:pointer;}
    button:disabled{opacity:.6; cursor:not-allowed;}
    .qrbox{display:flex; justify-content:center; margin:16px 0;}
    #qr{width:320px; height:320px; border-radius:12px; border:1px solid #eee; background:#fff;}
    .meta{font-size:13px; color:#333; line-height:1.5;}
    code{background:#f3f3f3; padding:3px 8px; border-radius:8px;}
    .hint{font-size:12px; color:#666; margin-top:10px;}
    .err{color:#b00020; white-space:pre-wrap;}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>PayWay QR (Sandbox)</h1>

      <div class="row" style="margin-bottom:10px;">
        <div>
          <label>Amount</label><br/>
          <input id="amount" value="1.00" inputmode="decimal" />
        </div>
        <div>
          <label>Currency</label><br/>
          <select id="currency">
            <option value="USD" selected>USD</option>
            <option value="KHR">KHR</option>
          </select>
        </div>
        <div>
          <label>Payment option</label><br/>
          <select id="payment_option">
            <option value="abapay_khqr" selected>ABA KHQR</option>
            <option value="wechat">WeChat (USD)</option>
            <option value="alipay">Alipay (USD)</option>
          </select>
        </div>
      </div>

      <div class="row" style="margin-bottom:10px;">
        <button id="btn" onclick="newQR()">Generate New QR</button>

        <label style="display:flex; gap:8px; align-items:center;">
          <input id="auto" type="checkbox" onchange="toggleAuto()" />
          Auto-refresh
        </label>

        <div>
          <label>Every (sec)</label><br/>
          <input id="interval" value="30" inputmode="numeric" style="width:90px;" />
        </div>
      </div>

      <div class="qrbox">
        <img id="qr" alt="QR will appear here" />
      </div>

      <div class="meta">
        Tran ID: <code id="tran">-</code><br/>
        Status: <code id="msg">-</code>
      </div>

      <div class="hint">
        Tip: For webhook.site testing, PayWay pushback goes to webhook.site. This page is only for generating QR.
      </div>

      <div id="error" class="err" style="margin-top:12px;"></div>
    </div>
  </div>

<script>
let timer = null;

function getPayload(){
  const amount = parseFloat(document.getElementById("amount").value || "1.00");
  const currency = document.getElementById("currency").value;
  const payment_option = document.getElementById("payment_option").value;

  return { amount, currency, payment_option };
}

async function newQR(){
  const btn = document.getElementById("btn");
  const err = document.getElementById("error");
  err.textContent = "";
  btn.disabled = true;

  try{
    const payload = getPayload();

    const res = await fetch("/create-qr", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if(!res.ok){
      err.textContent = "Error:\\n" + (data.error || JSON.stringify(data, null, 2));
      document.getElementById("msg").textContent = "ERROR";
      return;
    }

    // Update QR image and metadata
    document.getElementById("qr").src = data.qrImage;
    document.getElementById("tran").textContent = (data.status && data.status.tran_id) || data.tran_id || "-";
    document.getElementById("msg").textContent = (data.status && data.status.message) || "Success";
  } catch(e){
    err.textContent = "Error:\\n" + e.toString();
    document.getElementById("msg").textContent = "ERROR";
  } finally {
    btn.disabled = false;
  }
}

function toggleAuto(){
  const auto = document.getElementById("auto").checked;
  const intervalSec = Math.max(5, parseInt(document.getElementById("interval").value || "30", 10));

  if(timer){
    clearInterval(timer);
    timer = null;
  }

  if(auto){
    // generate immediately, then repeat
    newQR();
    timer = setInterval(newQR, intervalSec * 1000);
  }
}

// Auto-generate once on load
newQR();
</script>
</body>
</html>
"""


@app.post("/create-qr")
def create_qr_route():
    data = request.get_json(force=True) or {}

    amount = float(data["amount"])
    currency = (data.get("currency", "USD") or "USD").upper()
    payment_option = (data.get("payment_option", "abapay_khqr") or "abapay_khqr").lower()
    tran_id = data.get("tran_id") or datetime.now().strftime("trx%Y%m%d%H%M%S")

    try:
        resp = generate_qr(amount=amount, currency=currency, payment_option=payment_option, tran_id=tran_id)
        return jsonify(resp)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except requests.HTTPError as e:
        # Show PayWay error response (very helpful for debugging)
        try:
            return jsonify({"error": "PayWay HTTPError", "details": e.response.json()}), e.response.status_code
        except Exception:
            return jsonify({"error": "PayWay HTTPError", "details": e.response.text}), e.response.status_code

@app.get("/status/<tran_id>")
def status_route(tran_id: str):
    # With webhook.site, pushback won't hit this server.
    # So we verify status directly from PayWay.
    try:
        verified = check_transaction(tran_id)
        return jsonify({"verified": verified})
    except requests.HTTPError as e:
        try:
            return jsonify({"error": "PayWay HTTPError", "details": e.response.json()}), e.response.status_code
        except Exception:
            return jsonify({"error": "PayWay HTTPError", "details": e.response.text}), e.response.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
