import os
import io
import base64
import qrcode
from PIL import Image, ImageDraw, ImageFont

def generate_mock_khqr_base64(amount_usd, shop_name="Rabbit Cafe"):
    # 1. Image dimensions and styling
    width = 400
    height = 550
    bg_color = (255, 255, 255)
    header_color = (204, 25, 30) # KHQR Red

    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 2. Draw Top Red Header Toolbar 
    draw.rectangle([0, 0, width, 70], fill=header_color)
    
    # Try loading fonts, fallback to default
    try:
        font_large = ImageFont.truetype("arialbd.ttf", 36)
        font_medium = ImageFont.truetype("arial.ttf", 22)
        font_small = ImageFont.truetype("arial.ttf", 16)
        font_header = ImageFont.truetype("arialbd.ttf", 28)
    except IOError:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_header = ImageFont.load_default()

    # Draw "KHQR" text in header (approximate logo look)
    khqr_text = "KHQR"
    bbox = draw.textbbox((0, 0), khqr_text, font=font_header)
    w = bbox[2] - bbox[0]
    draw.text(((width - w) / 2, 20), khqr_text, fill=(255, 255, 255), font=font_header)
    
    # Optional styling: bottom right red triangle tab (like in some designs)
    draw.polygon([(width-40, 70), (width, 70), (width, 110)], fill=header_color)

    # 3. Draw Shop Name and Amount
    draw.text((30, 90), shop_name, fill=(50, 50, 50), font=font_medium)
    
    amount_text = f"$ {amount_usd:.2f}"
    draw.text((30, 125), amount_text, fill=(0, 0, 0), font=font_large)

    # 4. Draw Dashed separator line
    dash_length = 5
    for x in range(20, width - 20, dash_length * 2):
        draw.line([(x, 185), (x + dash_length, 185)], fill=(200, 200, 200), width=2)

    # 5. Generate actual QR code (Pointless data but looks real)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H, # High error correction to allow center logo
        box_size=10,
        border=1,
    )
    qr.add_data(f"MOCK_KHQR_DATA_FOR_AMOUNT_{amount_usd}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Resize QR to fit nicely
    qr_size = 300
    qr_img = qr_img.resize((qr_size, qr_size))
    
    # 6. Paste QR code into main image
    qr_x = (width - qr_size) // 2
    qr_y = 210
    img.paste(qr_img, (qr_x, qr_y))

    # 7. Draw the central Red Logo inside the QR code
    logo_size = 50
    logo_x = qr_x + (qr_size - logo_size) // 2
    logo_y = qr_y + (qr_size - logo_size) // 2
    
    # White background for logo circle
    draw.ellipse([logo_x-5, logo_y-5, logo_x+logo_size+5, logo_y+logo_size+5], fill=(255,255,255))
    # Red circle
    draw.ellipse([logo_x, logo_y, logo_x+logo_size, logo_y+logo_size], fill=header_color)
    # White C in middle
    bbox = draw.textbbox((0, 0), "C", font=font_medium)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((logo_x + (logo_size - w)/2, logo_y + (logo_size - h)/2 - 2), "C", fill=(255, 255, 255), font=font_medium)

    # 8. Encode to Base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # Return as data URI
    return f"data:image/png;base64,{img_str}"

if __name__ == "__main__":
    # Test generation
    b64 = generate_mock_khqr_base64(40.00)
    print("Base64 string starts with:", b64[:50])
