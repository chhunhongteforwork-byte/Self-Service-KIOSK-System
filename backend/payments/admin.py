from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    readonly_fields = ('created_at', 'payload_hash', 'aba_transaction_ref')
