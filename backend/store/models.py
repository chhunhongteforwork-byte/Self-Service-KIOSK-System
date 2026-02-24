from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.ImageField(upload_to='categories/', null=True, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    price = models.IntegerField(help_text="Price in cents (e.g., 100 = $1.00)")
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Paid'),
        ('PREPARING', 'Preparing'),
        ('SERVED', 'Served'),
        ('CANCELLED', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_amount = models.IntegerField(help_text="Total in cents")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.order_number} - {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    price_at_time = models.IntegerField(help_text="Price per unit in cents at time of purchase")

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def line_total(self):
        return self.quantity * self.price_at_time

from django.utils import timezone

class Receipt(models.Model):
    SOURCE_CHOICES = [
        ('REAL', 'Real'),
        ('SIMULATED', 'Simulated'),
    ]
    
    receipt_id = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    total_items = models.IntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='SIMULATED', db_index=True)

    def __str__(self):
        return f"Receipt {self.receipt_id}"

class ReceiptItem(models.Model):
    receipt = models.ForeignKey(Receipt, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    product_name_snapshot = models.CharField(max_length=255)
    category_snapshot = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    qty = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.qty}x {self.product_name_snapshot} ({self.receipt.receipt_id})"

    class Meta:
        indexes = [
            models.Index(fields=['receipt']),
            models.Index(fields=['product']),
            models.Index(fields=['category_snapshot']),
        ]
