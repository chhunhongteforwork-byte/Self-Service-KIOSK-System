import json
import os
from PIL import Image, ImageDraw, ImageFont

categories = [
    "Signature", "Sparking Caffeine", "Basic", "Matcha",
    "Chocolate", "Tea", "Smoothie", "Weird Series"
]
products = [
    "Golden latte", "Island Coconut latte", "Silk Cloud Latte", "Caramel butter Latte",
    "Vanilla Bloom Latte", "Jasmine Silk Latte", "Yuzu Spark Americano", "Orange Spark Americano",
    "Apple Fizz Americano", "Grape Fizz Americano", "Espresso", "House Americano",
    "Classic Cafe Latte", "Cappucino", "Mocha Latte", "Caramel Macchiato",
    "Matcha Latte", "Matcha Oat Latte", "Jasmine Matcha Frappe", "Silk Coconut Matcha Late",
    "Jasmine matcha Pistachio cream", "Matcha Caramel Machiato", "Silky Chocolate",
    "Coconut Chocolate Frappe", "Minty Chocolate Frappe", "Chocolate Frappe", "Classic Chocolate",
    "Ginger Honey Citrus Tea", "Valen Tea", "Berry peppermint Tea", "Strawberry",
    "Blueberry", "Mixed berries", "Mint Chocolate Espresso Float", "Lab Error 404",
    "Chocolate Matcha Fracture", "Grape Cold Brew Velvet", "Salted Matcha Caramel Reactor"
]

cat_colors = {
    "Signature": "#FFD700", "Sparking Caffeine": "#FF8C00", "Basic": "#8B4513",
    "Matcha": "#9ACD32", "Chocolate": "#D2691E", "Tea": "#F4A460",
    "Smoothie": "#FF69B4", "Weird Series": "#8A2BE2"
}

def create_placeholder(text, filename, bg_color):
    img = Image.new('RGB', (400, 400), color=bg_color)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        font = ImageFont.load_default()
    
    # Simple centered text
    text_bbox = d.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    position = ((400 - text_width) / 2, (400 - text_height) / 2)
    d.text(position, text, fill=(255, 255, 255), font=font)
    
    img.save(filename)

cat_dir = os.path.join("backend", "media", "categories")
prod_dir = os.path.join("backend", "media", "products")

for cat in categories:
    safe = cat.lower().replace(" ", "_")
    name = f"cat_{safe}.webp"
    path = os.path.join(cat_dir, name)
    if not os.path.exists(path):
        create_placeholder(cat, path, cat_colors.get(cat, "#333333"))

for prod in products:
    safe = prod.lower().replace(" ", "_") + ".webp"
    path = os.path.join(prod_dir, safe)
    if not os.path.exists(path):
        create_placeholder(prod, path, "#555555")

print("Placeholder images generated successfully.")
