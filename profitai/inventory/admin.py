from django.contrib import admin
from inventory.models import Product, Batches


class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name','brand')

admin.site.register(Product, ProductAdmin)

class BatchesAdmin(admin.ModelAdmin):
    list_display = ('product_id','remaining_quantity','sales_price','status','expiry_date')
    
admin.site.register(Batches, BatchesAdmin)  