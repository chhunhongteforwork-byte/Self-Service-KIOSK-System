import os
import sys
import django
from django.core.files import File

# Add current directory to path so we can import config and store
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from store.models import Category, Product
from django.conf import settings

if os.environ.get("SEED_DEMO_DATA", "").lower() != "true":
    print("Skipping seed demo data")
    sys.exit(0)

print("Seeding Data (Idempotent)...")

categories_data = [
    {"name": "Signature", "sort_order": 1, "image_name": "cat_signature.webp"},
    {"name": "Sparking Caffeine", "sort_order": 2, "image_name": "cat_sparking_caffeine.webp"},
    {"name": "Basic", "sort_order": 3, "image_name": "cat_basic.webp"},
    {"name": "Matcha", "sort_order": 4, "image_name": "cat_matcha.webp"},
    {"name": "Chocolate", "sort_order": 5, "image_name": "cat_chocolate.webp"},
    {"name": "Tea", "sort_order": 6, "image_name": "cat_tea.webp"},
    {"name": "Smoothie", "sort_order": 7, "image_name": "cat_smoothie.webp"},
    {"name": "Weird Series", "sort_order": 8, "image_name": "cat_weird_series.webp"},
]

products_data = [
    {"category": "Signature", "name": "Golden latte", "price": 450, "description": "A luxurious signature latte."},
    {"category": "Signature", "name": "Island Coconut latte", "price": 450, "description": "Tropical coconut latte."},
    {"category": "Signature", "name": "Silk Cloud Latte", "price": 450, "description": "Smooth and airy signature drink."},
    {"category": "Signature", "name": "Caramel butter Latte", "price": 450, "description": "Rich caramel and butter flavors."},
    {"category": "Signature", "name": "Vanilla Bloom Latte", "price": 450, "description": "Fragrant vanilla latte."},
    {"category": "Signature", "name": "Jasmine Silk Latte", "price": 450, "description": "Delicate jasmine floral latte."},
    {"category": "Sparking Caffeine", "name": "Yuzu Spark Americano", "price": 350, "description": "Zesty yuzu with a caffeine kick."},
    {"category": "Sparking Caffeine", "name": "Orange Spark Americano", "price": 350, "description": "Citrusy and refreshing coffee."},
    {"category": "Sparking Caffeine", "name": "Apple Fizz Americano", "price": 350, "description": "Crisp apple sparkling americano."},
    {"category": "Sparking Caffeine", "name": "Grape Fizz Americano", "price": 350, "description": "Sweet grape sparkling americano."},
    {"category": "Basic", "name": "Espresso", "price": 250, "description": "Strong, rich double shot."},
    {"category": "Basic", "name": "House Americano", "price": 300, "description": "Classic and balanced."},
    {"category": "Basic", "name": "Classic Cafe Latte", "price": 350, "description": "Smooth and creamy."},
    {"category": "Basic", "name": "Cappucino", "price": 350, "description": "Rich espresso with foamed milk."},
    {"category": "Basic", "name": "Mocha Latte", "price": 400, "description": "Coffee mixed with rich chocolate."},
    {"category": "Basic", "name": "Caramel Macchiato", "price": 400, "description": "Sweet caramel over espresso and milk."},
    {"category": "Matcha", "name": "Matcha Latte", "price": 400, "description": "Premium grade green tea with milk."},
    {"category": "Matcha", "name": "Matcha Oat Latte", "price": 450, "description": "Vegan-friendly creamy matcha."},
    {"category": "Matcha", "name": "Jasmine Matcha Frappe", "price": 500, "description": "Blended floral matcha treat."},
    {"category": "Matcha", "name": "Silk Coconut Matcha Late", "price": 450, "description": "Matcha with creamy coconut."},
    {"category": "Matcha", "name": "Jasmine matcha Pistachio cream", "price": 550, "description": "Rich pistachio cream top."},
    {"category": "Matcha", "name": "Matcha Caramel Machiato", "price": 500, "description": "Matcha combined with sweet caramel."},
    {"category": "Chocolate", "name": "Silky Chocolate", "price": 400, "description": "Smooth, rich hot chocolate."},
    {"category": "Chocolate", "name": "Coconut Chocolate Frappe", "price": 450, "description": "Blended tropical chocolate."},
    {"category": "Chocolate", "name": "Minty Chocolate Frappe", "price": 450, "description": "Refreshing mint and rich chocolate."},
    {"category": "Chocolate", "name": "Chocolate Frappe", "price": 400, "description": "Classic blended chocolate."},
    {"category": "Chocolate", "name": "Classic Chocolate", "price": 350, "description": "Our traditional recipe."},
    {"category": "Tea", "name": "Ginger Honey Citrus Tea", "price": 350, "description": "Soothing and citrusy."},
    {"category": "Tea", "name": "Valen Tea", "price": 350, "description": "Romantic floral tea blend."},
    {"category": "Tea", "name": "Berry peppermint Tea", "price": 350, "description": "Refreshing mint and mixed berries."},
    {"category": "Smoothie", "name": "Strawberry", "price": 400, "description": "Fresh strawberry blend."},
    {"category": "Smoothie", "name": "Blueberry", "price": 400, "description": "Antioxidant-rich blueberry."},
    {"category": "Smoothie", "name": "Mixed berries", "price": 450, "description": "Sweet and tart berry mix."},
    {"category": "Weird Series", "name": "Mint Chocolate Espresso Float", "price": 550, "description": "Ice cream, espresso and mint chocolate."},
    {"category": "Weird Series", "name": "Lab Error 404", "price": 600, "description": "A mysterious concoction."},
    {"category": "Weird Series", "name": "Chocolate Matcha Fracture", "price": 500, "description": "A split visual of matcha and chocolate."},
    {"category": "Weird Series", "name": "Grape Cold Brew Velvet", "price": 500, "description": "Fruity grape meets smooth cold brew."},
    {"category": "Weird Series", "name": "Salted Matcha Caramel Reactor", "price": 550, "description": "Explosive sweet, salty, earthy flavors."},
]

def get_image_file(category_or_product_dir, image_name):
    path = os.path.join(settings.BASE_DIR, 'media', category_or_product_dir, image_name)
    if os.path.exists(path):
        return path
    return None

stats = {
    "cat_created": 0, "cat_updated": 0, "cat_skipped": 0,
    "prod_created": 0, "prod_updated": 0, "prod_skipped": 0,
}

for cat_data in categories_data:
    obj, created = Category.objects.get_or_create(
        name=cat_data["name"],
        defaults={"sort_order": cat_data["sort_order"]}
    )
    
    changed = False
    if obj.sort_order != cat_data["sort_order"]:
        obj.sort_order = cat_data["sort_order"]
        changed = True

    # Check and attach image if available
    img_path = get_image_file('categories', cat_data["image_name"])
    if img_path and not obj.icon:
        with open(img_path, 'rb') as f:
            obj.icon.save(cat_data["image_name"], File(f), save=False)
        changed = True

    if created:
        if changed: obj.save()
        stats["cat_created"] += 1
    else:
        if changed:
            obj.save()
            stats["cat_updated"] += 1
        else:
            stats["cat_skipped"] += 1

for prod_data in products_data:
    cat = Category.objects.get(name=prod_data["category"])
    obj, created = Product.objects.get_or_create(
        category=cat,
        name=prod_data["name"],
        defaults={
            "price": prod_data["price"],
            "description": prod_data["description"]
        }
    )
    
    changed = False
    if obj.price != prod_data["price"]:
        obj.price = prod_data["price"]
        changed = True
    if obj.description != prod_data["description"]:
        obj.description = prod_data["description"]
        changed = True
        
    # Formatting generated product icon name: lowercase and spaces to underscores + webp
    safe_name = prod_data["name"].lower().replace(" ", "_") + ".webp"
    cat_safe_name = prod_data["category"].lower().replace(" ", "_") + ".webp"
    
    img_path = get_image_file('products', safe_name)
    if not img_path:
        img_path = get_image_file('products', cat_safe_name)
    
    if img_path and not obj.image:
        with open(img_path, 'rb') as f:
            obj.image.save(safe_name, File(f), save=False)
        changed = True
        
    if created:
        if changed: obj.save()
        stats["prod_created"] += 1
    else:
        if changed:
            obj.save()
            stats["prod_updated"] += 1
        else:
            stats["prod_skipped"] += 1

print("--- Seed Execution Summary ---")
print(f"Categories: {stats['cat_created']} created, {stats['cat_updated']} updated, {stats['cat_skipped']} skipped.")
print(f"Products: {stats['prod_created']} created, {stats['prod_updated']} updated, {stats['prod_skipped']} skipped.")
print("Seeding Complete!")
