from django.contrib import admin
from invoice.models import Invoice, InvoiceItem

class InvoiceItemData(admin.ModelAdmin):
    list_display = ('product','quantity','price')

class InvoiceData(admin.ModelAdmin):
    list_display = ('customer','Invoice_pdf','invoice_counter','order_date_time','grand_total','remaining_total','payment_type')
admin.site.register(Invoice, InvoiceData)
admin.site.register(InvoiceItem, InvoiceItemData)