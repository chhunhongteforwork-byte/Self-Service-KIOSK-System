from django.db import models
from store.models import Order

class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    order = models.ForeignKey(Order, related_name='payments', on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    amount = models.IntegerField(help_text="Amount in cents")
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payload_hash = models.CharField(max_length=255, null=True, blank=True)
    aba_transaction_ref = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order.order_number} - {self.status}"
