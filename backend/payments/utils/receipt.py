from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from io import BytesIO
from store.models import Order
from django.conf import settings
import datetime
import pytz
import os

def generate_order_receipt_pdf(order_id: int):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return None

    # Cambodia Time Adjustment
    cambodia_tz = pytz.timezone('Asia/Phnom_Penh')
    local_time = order.created_at.astimezone(cambodia_tz)

    buffer = BytesIO()
    width, height = (320, 650)
    p = canvas.Canvas(buffer, pagesize=(width, height)) 

    # --- Background Decoration ---
    # Soft pink background
    p.setFillColor(HexColor("#FFF0F5"))
    p.rect(0, 0, width, height, fill=1, stroke=0)
    
    # White main area with rounded corners
    p.setFillColor(HexColor("#FFFFFF"))
    p.setStrokeColor(HexColor("#FF69B4"))
    p.roundRect(10, 10, width-20, height-20, 15, fill=1, stroke=1)

    # --- Strawberry Background Pattern (Subtle) ---
    p.setFont("Helvetica", 30)
    p.setFillColor(HexColor("#FFB7C5")) # Very light pink
    p.setFillAlpha(0.15) # High transparency
    for i in range(5):
        for j in range(8):
            p.drawCentredString(40 + i*60, 40 + j*80, "🍓")
    p.setFillAlpha(1.0) # Reset transparency

    # --- Logo Placement ---
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'rabbit_logo.png')
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        # Center the logo at the top
        p.drawImage(logo, width/2 - 40, height - 100, width=80, height=80, mask='auto', preserveAspectRatio=True)
    
    # Move text down to avoid overlapping the logo
    header_y = height - 120

    # --- Header ---
    p.setFillColor(HexColor("#FF69B4"))
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width/2, header_y, "RABBIT KIOSK")
    
    p.setFont("Helvetica-BoldOblique", 11)
    p.setFillColor(HexColor("#FF8C00")) 
    p.drawCentredString(width/2, header_y - 20, "~ Freshly Brewed Happiness ~")

    p.setStrokeColor(HexColor("#FFB7C5"))
    p.setDash(4, 2)
    p.line(30, header_y - 35, width - 30, header_y - 35)
    p.setDash(1, 0)

    # --- Order Info ---
    p.setFillColor(HexColor("#4A4A4A"))
    p.setFont("Helvetica-Bold", 11)
    p.drawString(35, header_y - 60, f"RECEIPT: {order.order_number}")
    
    p.setFont("Helvetica", 10)
    p.drawString(35, header_y - 80, f"Date: {local_time.strftime('%d %b %Y, %I:%M %p')}")
    p.drawString(35, header_y - 95, f"Region: Cambodia (GMT+7)")

    p.setStrokeColor(HexColor("#FFB7C5"))
    p.line(30, header_y - 110, width - 30, header_y - 110)

    # --- Items ---
    y = header_y - 135
    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(HexColor("#FF69B4"))
    p.drawString(35, y, "MENU ITEM")
    p.drawRightString(width - 35, y, "PRICE")
    
    y -= 25
    p.setFillColor(HexColor("#4A4A4A"))
    p.setFont("Helvetica", 11)
    
    for item in order.items.all():
        name = f"{item.quantity}x {item.product.name}"
        p.drawString(35, y, name)
        
        price_str = f"${(item.line_total / 100.0):.2f}"
        p.drawRightString(width - 35, y, price_str)
        
        y -= 22
        if y < 150: break

    # --- Totals ---
    p.setStrokeColor(HexColor("#FF69B4"))
    p.line(30, y + 5, width - 30, y + 5)
    y -= 35
    
    p.setFillColor(HexColor("#FF69B4"))
    p.setFont("Helvetica-Bold", 18)
    p.drawString(35, y, "TOTAL DUE")
    p.drawRightString(width - 35, y, f"${(order.total_amount / 100.0):.2f}")

    # --- Footer ---
    y -= 60
    p.setFont("Helvetica-BoldOblique", 12)
    p.setFillColor(HexColor("#FF8C00"))
    p.drawCentredString(width/2, y, "Hop back in soon!")
    
    # Bottom Icons
    p.setFont("Helvetica", 14)
    p.drawCentredString(width/2, 40, "🍓  🐰  🍓")

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer
