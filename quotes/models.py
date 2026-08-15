from django.contrib.auth.models import User
from django.db import models

from chemsapp.models import Customer, DilutionVariant, ProductVariant


def generate_quote_number():
    """Sequential human-facing quote numbers: Q0001, Q0002, ..."""
    last = Quote.objects.filter(quote_number__startswith='Q').order_by('-quote_number').first()
    if last:
        try:
            return f'Q{int(last.quote_number[1:]) + 1:04d}'
        except ValueError:
            pass
    return 'Q0001'


class Quote(models.Model):
    quote_number = models.CharField(max_length=10, unique=True, editable=False)
    company_name = models.CharField(max_length=255)
    address = models.TextField(blank=True, default='')
    contact_name = models.CharField(max_length=255, blank=True, default='')
    # Optional provenance link when the header was prefilled from an existing customer
    customer = models.ForeignKey(Customer, related_name='quotes', on_delete=models.SET_NULL, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='quotes_created', on_delete=models.SET_NULL, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    pdf = models.FileField(upload_to='quote_pdfs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.quote_number:
            self.quote_number = generate_quote_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Proposal {self.quote_number} — {self.company_name}'


class QuoteLine(models.Model):
    quote = models.ForeignKey(Quote, related_name='lines', on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, related_name='quote_lines', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sort_order = models.PositiveIntegerField(default=0)
    # Dilution options the salesperson picked for this line; the source used
    # to (re-)freeze the cost_in_use snapshot below.
    dilutions = models.ManyToManyField(DilutionVariant, blank=True, related_name='quote_lines')

    # Snapshots frozen at generation time so old proposals never drift
    # when product data changes later.
    product_name = models.CharField(max_length=255)
    product_subheading = models.CharField(max_length=255, blank=True, default='')
    product_code = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    # Product.wall_chart_color at generation time. Blank means the PDF uses
    # the neutral grey row.
    row_color = models.CharField(max_length=7, blank=True, default='')
    cost_in_use = models.JSONField(default=list, blank=True)
    # e.g. [{"label": "Floor Mop/Bucket - General Cleaning", "unit_label": "per litre",
    #        "fills": "200.00", "cost": "0.45", "display": "Floor Mop/Bucket - General Cleaning .45c"}]

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.product_name} @ ${self.price}'
