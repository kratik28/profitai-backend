from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from user_profile.models import UserProfile, BusinessProfile, Customer, UserProfileOTP

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ['action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message']
    search_fields = ['user__username', 'object_repr', 'change_message']
    list_filter = ['content_type']

admin.site.register(Permission)
admin.site.register(ContentType)
admin.site.register(Session)

class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'get_user_permissions']

    def get_user_permissions(self, obj):
        return ", ".join([perm.codename for perm in obj.user_permissions.all()])

    get_user_permissions.short_description = 'User Permissions'

# admin.site.unregister(User)
# admin.site.register(User, UserAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'phone_number', 'last_login', 'is_active', 'created_at', 'updated_at']
class BusinessProfileData(admin.ModelAdmin):
    list_display = ['user_profile','business_number','business_name','business_type','gst_number','email']
class CustomerData(admin.ModelAdmin):
    list_display = ['business_profile','customer_name','phone_number','email']
class UserProfileOTPData(admin.ModelAdmin):
    list_display = ['user_profile','phone_number','otp','is_verified']
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(BusinessProfile,BusinessProfileData)
admin.site.register(Customer,CustomerData)
admin.site.register(UserProfileOTP,UserProfileOTPData)