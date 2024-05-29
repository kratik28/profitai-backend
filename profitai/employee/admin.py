from django.contrib import admin
from .models import Employee, Attendance

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'location', 'role', 'date_of_joining', 'salary', 'is_active', 'business_profile')
    search_fields = ('name', 'contact_number', 'role')
    list_filter = ('location', 'role', 'is_active', 'business_profile')

admin.site.register(Employee, EmployeeAdmin)

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in_time', 'check_out_time', 'status', 'business_profile')
    search_fields = ('employee__name', 'date', 'status')
    list_filter = ('status', 'date', 'business_profile')

admin.site.register(Attendance, AttendanceAdmin)
