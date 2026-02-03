import os
import sys
import django

# Add current directory to path so we can import config and store
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from store.models import Category, Product

# Clear existing
print("Clearing data...")
Product.objects.all().delete()
Category.objects.all().delete()

print("Seeding Data...")

cat_coffee = Category.objects.create(name="Coffee", sort_order=1)
cat_tea = Category.objects.create(name="Tea & Match", sort_order=2)
cat_bakery = Category.objects.create(name="Bakery", sort_order=3)

Product.objects.create(category=cat_coffee, name="Iced Cappuccino", price=250, description="Rich and creamy")
Product.objects.create(category=cat_coffee, name="Hot Latte", price=250, description="Smooth and milky")
Product.objects.create(category=cat_coffee, name="Americano", price=200, description="Strong kick")

Product.objects.create(category=cat_tea, name="Matcha Latte", price=300, description="Premium Japanese Matcha")
Product.objects.create(category=cat_tea, name="Lemon Tea", price=200, description="Refreshing")

Product.objects.create(category=cat_bakery, name="Croissant", price=150, description="Buttery")
Product.objects.create(category=cat_bakery, name="Chocolate Muffin", price=200, description="Decadent")

print("Seeded!")
