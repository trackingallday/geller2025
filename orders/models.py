import random
import string
from django.db import models
from chemsapp.models import Customer, ProductVariant


FULFILMENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('fulfilled', 'Fulfilled'),
    ('cancelled', 'Cancelled'),
]


def generate_order_number():
    while True:
        letters = ''.join(random.choices(string.ascii_uppercase, k=2))
        digits = ''.join(random.choices(string.digits, k=4))
        candidate = letters + digits
        if not CustomerOrder.objects.filter(order_number=candidate).exists():
            return candidate


class CustomerOrder(models.Model):
    customer = models.ForeignKey(Customer, related_name='orders', on_delete=models.CASCADE)
    order_number = models.CharField(max_length=6, unique=True, editable=False)
    date = models.DateTimeField(auto_now_add=True)
    fulfilment_status = models.CharField(
        max_length=20,
        choices=FULFILMENT_STATUS_CHOICES,
        default='pending',
    )
    pdf = models.FileField(upload_to='order_pdfs/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    submitted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Order {self.order_number} — {self.customer}'


class OrderLineItem(models.Model):
    order = models.ForeignKey(CustomerOrder, related_name='line_items', on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, related_name='order_line_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.product_variant} x{self.quantity}'
