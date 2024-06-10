from django.db import models
import uuid
from django.db.models.signals import pre_save
from django.dispatch import receiver
from user_profile.models import BusinessProfile
from inventory.models import Product


# Create your models here.
class BusinessInventoryLink(models.Model):
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, null=False)
    products = models.ManyToManyField(Product)
    unique_link_code = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['unique_link_code']),
            models.Index(fields=['business_profile']),
        ]

    def __str__(self):
        return f"Link Code: {self.unique_link_code} for Business: {self.business_profile.business_name}"

    def add_product(self, product):
        self.products.add(product)
        self.save()

    def remove_product(self, product):
        self.products.remove(product)
        self.save()

@receiver(pre_save, sender=BusinessInventoryLink)
def generate_unique_link_code(sender, instance, **kwargs):
    if not instance.unique_link_code:
        instance.unique_link_code = str(uuid.uuid4())