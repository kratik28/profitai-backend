from django.contrib import admin
from .models import Expense

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_name', 'cost', 'date', 'paid_to', 'category', 'business_profile', 'created_at', 'updated_at')
    search_fields = ('expense_name', 'paid_to', 'category__name', 'business_profile__name')
    list_filter = ('date', 'category', 'business_profile')
    ordering = ('-date',)

admin.site.register(Expense, ExpenseAdmin)
