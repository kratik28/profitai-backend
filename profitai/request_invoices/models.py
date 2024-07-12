from django.db import models
import uuid
import datetime
from user_profile.models import BusinessProfile, Vendor


class RequestInvoice(models.Model):
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, null=False)
    date_time = models.DateTimeField(default=None, null=True, blank=True)
    vendor= models.ForeignKey(Vendor, on_delete=models.CASCADE, null=False)
    is_deleted = models.BooleanField(default=False)
    Invoice_pdf = models.FileField(upload_to='request_invoice_pdf/', blank=True, null=True)
    invoice_counter = models.CharField(max_length=30, default=None, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def generate_transaction_id(self):
        timestamp = datetime.datetime.now().strftime('%y%m%d%H')
        unique_id = uuid.uuid4().hex[:4]
        return f'{timestamp}{unique_id.upper()}'

    def save(self, *args, **kwargs):
        if not self.invoice_counter:
            try:
                self.invoice_counter = self.generate_transaction_id()
            except Exception as e:
                print(f"Error generating transaction ID: {e}")
        super(RequestInvoice, self).save(*args, **kwargs)

class RequestInvoiceProduct(models.Model):
    request_invoice = models.ForeignKey(RequestInvoice, related_name='products', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255, null=False, blank=False)
    brand = models.CharField(max_length=255, null=False, blank=False)
    qty = models.IntegerField(null=False, blank=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
