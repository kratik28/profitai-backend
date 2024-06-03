from django.db import models
from user_profile.models import BusinessProfile

class Employee(models.Model):
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="employees")
    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    location = models.CharField(max_length=100)
    address = models.TextField()
    role = models.CharField(max_length=50)
    date_of_joining = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    email = models.EmailField(max_length=254, unique=True, null=True)  # Add email field
    holidays = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.business_profile.business_name})"

class Attendance(models.Model):
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="attendances")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendances")
    date = models.DateField()
    check_in_time = models.TimeField()
    check_out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Leave', 'Leave')], default='Present')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.employee.name} - {self.date}"
