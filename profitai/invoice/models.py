import datetime
import uuid
from django.db import models
from user_profile.models import BusinessProfile, Customer, Vendor
from inventory.models import Product, Batches

class Invoice(models.Model):
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, null=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)
    vendor= models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    invoice_counter = models.CharField(max_length=30, default=None, null=True, blank=True)
    order_date_time = models.DateTimeField(default=None, null=True, blank=True)
    status = models.IntegerField(default=None, blank=True, null=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    remaining_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    payment_option = models.CharField(max_length=50,null=True,blank=True,default=None)
    payment_type =models.CharField(max_length=50,null=True,blank=True,default=None)
    description = models.TextField(max_length=100, null=True, default=None, blank=True)
    Invoice_pdf = models.FileField(upload_to='invoice_pdf/', blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    is_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_transaction_id(self):
        # Use a combination of current timestamp and a unique identifier
        timestamp = datetime.datetime.now().strftime('%y%m%d%H')
        unique_id = uuid.uuid4().hex[:4]  # Use the first 4 characters of a random UUID
        return f'{timestamp}{unique_id.upper()}'

    def save(self, *args, **kwargs):
        if not self.invoice_counter:  # Check if invoice_counter is empty or not set
            try:
                self.invoice_counter = self.generate_transaction_id()
            except Exception as e:
                # Handle the exception (e.g., log the error)
                print(f"Error generating transaction ID: {e}")

        super(Invoice, self).save(*args, **kwargs)
    def __str__(self) -> str:
        customer_name = self.customer.customer_name if self.customer else "No customer"
        vendor_name = self.vendor.vendor_name if self.vendor else "No vendor"
        return f"Invoice customer {customer_name} or vendor {vendor_name}, id {self.invoice_counter}"

        
        
class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, null=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)
    batch = models.ForeignKey(Batches, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(default=None, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self) -> str:
        return f"InvoiceItem customer {self.invoice.customer.customer_name} product {self.product.product_name}"
        