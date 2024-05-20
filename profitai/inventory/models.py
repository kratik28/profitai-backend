from django.db import models
from user_profile.models import BusinessProfile
from master_menu.models import ProductType

class Product(models.Model):
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, null=False)
    product_name = models.CharField(max_length=50, null=False, default=None, blank=False)
    brand = models.CharField(max_length=50,default=None, null=True, blank=True)
    product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"product_name: {self.product_name}"
    
class Batches(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, related_name='batches')
    size = models.CharField(max_length=50, default=None, null=True, blank=True)
    total_quantity = models.IntegerField(default=None, blank=True, null=True)
    remaining_quantity = models.IntegerField(default=None, blank=True, null=True)
    sales_price = models.CharField(max_length=50, null=True, default=None, blank=True)
    mrp_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    add_margin = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None, blank=True)
    status = models.IntegerField(default=None, blank=True, null=True)
    bar_code_number = models.CharField(max_length=50, null=True, blank=True, default=None)
    hsn_number = models.CharField(max_length=50, null=True, blank=True, default=None)
    batch_number = models.CharField(max_length=50, null=True, blank=True, default=None)
    package = models.CharField(max_length=50, null=True, blank=True, default=None)
    expiry_date = models.DateTimeField(default=None, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"batch_number: {self.batch_number}"
