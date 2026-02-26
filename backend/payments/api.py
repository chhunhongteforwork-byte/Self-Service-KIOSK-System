from ninja import Router, Schema
from typing import List
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from store.models import Order, OrderItem, Product, Receipt, ReceiptItem
from .models import Payment
from .utils.aba_payway import generate_qr, check_transaction
from .utils.receipt import generate_order_receipt_pdf
import uuid

router = Router()

class CartItemSchema(Schema):
    product_id: int
    quantity: int

class CheckoutRequest(Schema):
    items: List[CartItemSchema]
    total_amount: int # Client calculated, we should verify server side ideally

class CheckoutResponse(Schema):
    order_id: int
    order_number: str
    qr_data: dict # Contains qr_image url etc
    total_amount: int
from django.conf import settings
from django.utils import timezone
from .utils.mock_qr import generate_mock_khqr_base64

@router.post("/checkout", response=CheckoutResponse)
def checkout(request, payload: CheckoutRequest):
    # 1. Create Order
    # Unique order number
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    order = Order.objects.create(
        order_number=order_number,
        status='PENDING',
        total_amount=0 # Will update
    )
    
    calculated_total = 0
    items_for_aba = []
    
    for item in payload.items:
        product = get_object_or_404(Product, id=item.product_id)
        line_total = product.price * item.quantity
        calculated_total += line_total
        
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item.quantity,
            price_at_time=product.price
        )
        
        items_for_aba.append({
            "name": product.name,
            "quantity": item.quantity,
            "price": str(product.price / 100.0) 
        })
        
    order.total_amount = calculated_total
    order.save()
    
    # 2. Call ABA Generate QR
    tran_id = f"TRX-{order.order_number}"
    amount_usd = calculated_total / 100.0
    
    try:
        qr_response = generate_qr(
            amount=amount_usd,
            currency="USD",
            payment_option="abapay_khqr",
            tran_id=tran_id
        )
    except Exception as e:
        if settings.DEBUG:
            print("WARNING: ABA PayWay API failed. Using beautiful mock Rabbit Cafe KHQR for local dev.")
            
            # Generate the dynamic base64 KHQR image matching the requested style
            b64_img = generate_mock_khqr_base64(amount_usd, shop_name="Rabbit Cafe")
            
            qr_response = {
                "hash": "mock_hash_123",
                "qrImage": b64_img
            }
        else:
            raise e
    
    # 3. Create Payment Record
    Payment.objects.create(
        order=order,
        transaction_id=tran_id,
        amount=calculated_total,
        status='PENDING',
        payload_hash=qr_response.get('hash', '')
    )
    
    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "qr_data": qr_response,
        "total_amount": calculated_total
    }

class OrderStatusResponse(Schema):
    order_id: int
    status: str
    payment_status: str

class SuccessResponse(Schema):
    success: bool

def sync_order_to_receipt(order: Order):
    if Receipt.objects.filter(receipt_id=order.order_number).exists():
        return
        
    receipt = Receipt.objects.create(
        receipt_id=order.order_number,
        total_items=sum(item.quantity for item in order.items.all()),
        total_amount=order.total_amount / 100.0,
        source='REAL'
    )
    
    for item in order.items.all():
        ReceiptItem.objects.create(
            receipt=receipt,
            product=item.product,
            product_name_snapshot=item.product.name if item.product else "Unknown Product",
            category_snapshot=item.product.category.name if item.product and item.product.category else "Unknown",
            qty=item.quantity,
            unit_price=item.price_at_time / 100.0,
            line_total=item.line_total / 100.0
        )

@router.post("/orders/{order_id}/mock-pay", response=SuccessResponse)
def mock_pay_order(request, order_id: int):
    val_order = get_object_or_404(Order, id=order_id)
    if settings.DEBUG and val_order.status == 'PENDING':
        payment = val_order.payments.last()
        if payment:
            payment.status = 'COMPLETED'
            payment.save()
        val_order.status = 'PAID'
        val_order.save()
        sync_order_to_receipt(val_order)
    return {"success": True}

@router.get("/orders/{order_id}/status", response=OrderStatusResponse)
def check_order_status(request, order_id: int):
    val_order = get_object_or_404(Order, id=order_id)
    
    # Logic to poll ABA if pending
    if val_order.status == 'PENDING':
        payment = val_order.payments.last()
        if payment and payment.status == 'PENDING':
            # Check ABA
             try:
                res = check_transaction(payment.transaction_id)
                code = res.get('status', {}).get('code')
             except Exception as e:
                 if not settings.DEBUG:
                     print(f"Error checking ABA: {e}")
                 code = "99" # Keep as pending unless ABA says otherwise or manual mock-pay is triggered
                     
             if code == "00":
                 payment.status = 'COMPLETED'
                 payment.save()
                 val_order.status = 'PAID'
                 val_order.save()
                 sync_order_to_receipt(val_order)
                 
    return {
        "order_id": val_order.id,
        "status": val_order.status,
        "payment_status": val_order.payments.last().status if val_order.payments.exists() else 'NONE'
    }

@router.get("/orders/{order_id}/receipt")
def download_receipt(request, order_id: int):
    buffer = generate_order_receipt_pdf(order_id)
    if not buffer:
        return {"error": "Order not found"}, 404
    
    return FileResponse(
        buffer, 
        as_attachment=True, 
        filename=f"receipt_order_{order_id}.pdf",
        content_type='application/pdf'
    )
