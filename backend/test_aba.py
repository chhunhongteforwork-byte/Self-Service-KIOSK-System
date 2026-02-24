import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
import requests
from payments.utils.aba_payway import generate_qr

try:
    generate_qr(amount=5.0, currency='USD', payment_option='abapay_khqr', tran_id='TRX-TEST999')
except requests.exceptions.HTTPError as e:
    with open('aba_error.txt', 'w') as f:
        f.write(e.response.text)
except Exception as e:
    with open('aba_error.txt', 'w') as f:
        f.write(str(e))
