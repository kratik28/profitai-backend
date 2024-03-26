from django.db import models

class BusinessType(models.Model):
    business_type = models.CharField(max_length=50, null=True, default=None, blank=True)
    type = models.CharField(max_length=50, null=True, default=None, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.business_type
      
class Industry(models.Model):
    industry_name = models.CharField(max_length=50, null=True, default=None, blank=True)
    type = models.CharField(max_length=50, null=True, default=None, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.industry_name
      
class ProductType(models.Model):
    category_name = models.CharField(max_length=50, null=True, default=None, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.category_name
      
class Brand(models.Model):
    brand_name = models.CharField(max_length=50, null=True, default=None, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.brand_name
      
class Size(models.Model):
    size = models.CharField(max_length=50, null=True, default=None, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.size