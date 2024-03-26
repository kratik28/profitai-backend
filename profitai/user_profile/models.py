from django.db import models
import secrets
from master_menu.models import BusinessType, Industry
from django.contrib.auth.models import AbstractUser 

class UserProfile(AbstractUser):
    phone_number = models.CharField(max_length=20, null=True, default=None, blank=True, unique=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    last_login = models.DateTimeField(default=None, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def validate_otp(self, user, otp):
        check_otp = UserProfileOTP.objects.filter(user_profile=user,phone_number=user.phone_number,otp=otp,is_verified=False).first()
        if check_otp:
            check_otp.is_verified = True
            check_otp.save()
            return True
        else:
            return False
    
    # REQUIRED_FIELDS = []
    # USERNAME_FIELD = 'username'
    
    # @property
    # def is_anonymous(self):
    #     return False

    # @property
    # def is_authenticated(self):
    #     return True
    
    def __str__(self):
        return f"phone_number: {self.phone_number}"
    
class UserProfileOTP(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=False)
    phone_number = models.CharField(max_length=20, null=False, default=None, blank=False)
    otp = models.IntegerField(default=None, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self) -> str:
        return str(self.otp)

class BusinessProfile(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=False)
    business_number = models.CharField(max_length=20, null=True, default=None, blank=True)
    business_name = models.CharField(max_length=50, null=True, default=None, blank=True)
    business_type = models.ForeignKey(BusinessType, on_delete=models.CASCADE, related_name="business_profiles", null=False)
    other_business_type = models.ForeignKey(BusinessType, on_delete=models.CASCADE, related_name="other_business_profiles", null=True, default=None, blank=True)
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE,related_name="business_profiles", null=False)
    other_industry_type = models.ForeignKey(Industry, on_delete=models.CASCADE,related_name="other_industry_profiles", null=True, default=None, blank=True)
    gst_number = models.CharField(max_length=50, null=True, default=None, blank=True)
    zipcode = models.CharField(max_length=10, null=True, default=None, blank=True)
    city = models.CharField(max_length=100, null=True, default=None, blank=True)
    state = models.CharField(max_length=100, null=True, default=None, blank=True)
    address1 = models.CharField(max_length=100, null=True, default=None, blank=True)
    address2 = models.CharField(max_length=100, null=True, default=None, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"business_name: {self.business_name}"
    
class Customer(models.Model):
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, null=False)
    customer_name = models.CharField(max_length=50, null=False, default=None, blank=False)
    address = models.CharField(max_length=100, null=False, default=None, blank=False)
    zipcode = models.CharField(max_length=100, null=False, default=None, blank=False)
    phone_number = models.CharField(max_length=20, null=False, default=None, blank=False)
    gst_number = models.CharField(max_length=50, null=True, default=None, blank=True)
    favourite = models.BooleanField(default=False)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"customer_name: {self.customer_name}"
    