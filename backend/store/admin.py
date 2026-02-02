from django.contrib import admin
from .models import Category, Product, Order, OrderItem

class ProductInline(admin.TabularInline):
    model = Product
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'sort_order')
    inlines = [ProductInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'active')
    list_filter = ('category', 'active')
    search_fields = ('name',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('line_total',)
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]
    readonly_fields = ('total_amount', 'order_number')
