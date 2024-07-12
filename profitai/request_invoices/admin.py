from django.contrib import admin
from request_invoices.models import RequestInvoice, RequestInvoiceProduct

class InvoiceItemData(admin.ModelAdmin):
    list_display = ('product_name','brand','qty')

class InvoiceData(admin.ModelAdmin):
    list_display = ('vendor','Invoice_pdf','invoice_counter','date_time')

admin.site.register(RequestInvoice, InvoiceData)
admin.site.register(RequestInvoiceProduct, InvoiceItemData)