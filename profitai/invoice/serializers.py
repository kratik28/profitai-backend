from rest_framework import serializers

from inventory.models import Product
from .models import Invoice, InvoiceItem
from user_profile.serializers import CustomerPdfSerializer

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'
    

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = '__all__'

class InvoiceCreateSerializer(serializers.ModelSerializer):
    customer = CustomerPdfSerializer()
    class Meta:
        model = Invoice
        fields = [ "id","invoice_counter","is_purchase", "order_date_time","status","grand_total","sub_total","paid_amount","remaining_total","tax","discount","payment_type",'payment_option',"Invoice","description","is_deleted","created_at","updated_at","customer"]

    Invoice = serializers.SerializerMethodField()

    def get_Invoice(self, obj):
      current_domain = self.context.get('current_domain', '')
      return f"{current_domain}/{obj.Invoice_pdf}" if current_domain else obj.Invoice_pdf
    


class ProductdataSerializer(serializers.ModelSerializer):
    quantity = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ["id", "product_name", "brand", "size", "total_quantity", "remaining_quantity",
                  "sales_price", "purchase_price", "tax", "discount", "status", "BAR_code_number", 
                  "batch_number", "expiry_date", "created_at", "updated_at","quantity"]

    def get_quantity(self, instance):
        invoice_items = instance.invoiceitem_set.all()
        total_quantity = invoice_items.filter(invoice=self.context['invoice'].id).last().quantity

        return total_quantity