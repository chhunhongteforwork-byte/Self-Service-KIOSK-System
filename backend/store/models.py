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
