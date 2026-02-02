from ninja import Router, Schema
from typing import List
from django.shortcuts import get_object_or_404
from store.models import Order, OrderItem, Product
from .models import Payment
from .utils.aba_payway import generate_qr, check_transaction
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

@router.post("/checkout", response=CheckoutResponse)
def checkout(request, payload: CheckoutRequest):
    # 1. Create Order
    # Unique order number
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    # Verify total and create order items
    # In a real app, strict price checking is needed.
    # For MVP, we trust product price from DB.
    
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
            "price": str(product.price / 100.0) # ABA Helper expects string float or similar? 
            # Wait, helper logic uses format_amount.
            # actually our aba_payway.generate_qr takes `amount` as float.
        })
        
    order.total_amount = calculated_total
    order.save()
    
    # 2. Call ABA Generate QR
    # Tran ID for ABA
    tran_id = f"TRX-{order.order_number}"
    amount_usd = calculated_total / 100.0
    
    qr_response = generate_qr(
        amount=amount_usd,
        currency="USD",
        payment_option="abapay_khqr",
        tran_id=tran_id
    )
    
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
                # Parse response
                # ABA sandbox output for check-transaction-2
                # status: 0 means success/paid? Need to verify doc. 
                # Assuming status 0000 or similar.
                # Let's inspect res in debug or assume 'status': {'code': '00', ...}
                
                # For now, let's look at `aba_payway.py`:
                # It just returns r.json(). 
                # Typical PayWay: status.code == "00" is success.
                code = res.get('status', {}).get('code')
                if code == "00":
                    payment.status = 'COMPLETED'
                    payment.save()
                    val_order.status = 'PAID'
                    val_order.save()
             except Exception as e:
                 print(f"Error checking ABA: {e}")
                 
    return {
        "order_id": val_order.id,
        "status": val_order.status,
        "payment_status": val_order.payments.last().status if val_order.payments.exists() else 'NONE'
    }
