from django.contrib import admin
from inventory.models import Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name','brand','remaining_quantity','sales_price','status','expiry_date')

admin.site.register(Product, ProductAdmin)
