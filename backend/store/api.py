from ninja import Router, Schema
from typing import List, Optional
from .models import Category, Product

router = Router()

class CategorySchema(Schema):
    id: int
    name: str
    icon_url: Optional[str] = None
    sort_order: int

    @staticmethod
    def resolve_icon_url(obj):
        if obj.icon:
            return obj.icon.url
        return None

class ProductSchema(Schema):
    id: int
    category_id: int
    name: str
    price: int
    description: str = ""
    image_url: Optional[str] = None
    active: bool

    @staticmethod
    def resolve_image_url(obj):
        if obj.image:
            return obj.image.url
        return None

@router.get("/categories", response=List[CategorySchema])
def list_categories(request):
    return Category.objects.all()

@router.get("/products", response=List[ProductSchema])
def list_products(request, category_id: Optional[int] = None):
    qs = Product.objects.filter(active=True)
    if category_id:
        qs = qs.filter(category_id=category_id)
    return qs
