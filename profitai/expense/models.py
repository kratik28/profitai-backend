from django.db import models
from user_profile.models import BusinessProfile

class Expense(models.Model):
    business_profile = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="expenses")
    date = models.DateField()
    expense_name = models.CharField(max_length=255)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    paid_to = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.expense_name} - {self.cost} on {self.date}"

    class Meta:
        ordering = ['-date']