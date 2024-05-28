from rest_framework import serializers

from inventory.models import Product
from .models import Invoice, InvoiceItem
from user_profile.serializers import CustomerPdfSerializer, VendorPdfSerializer
from inventory.serializers import BatchSerializer

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
    vendor = VendorPdfSerializer()
    class Meta:
        model = Invoice
        fields = [ "id","invoice_counter","is_purchase", "order_date_time","status","grand_total","sub_total","paid_amount","remaining_total","tax","discount","payment_type",'payment_option',"Invoice","description","is_deleted","created_at","updated_at","customer", "vendor"]

    Invoice = serializers.SerializerMethodField()

    def get_Invoice(self, obj):
      current_domain = self.context.get('current_domain', '')
      return f"{current_domain}/{obj.Invoice_pdf}" if current_domain else obj.Invoice_pdf
    


class ProductdataSerializer(serializers.ModelSerializer):
    invoice_items = serializers.SerializerMethodField()
    total_remaining_quantity = serializers.IntegerField(read_only=True)
    batches = BatchSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id', 'product_name', 'total_remaining_quantity','batches', 'invoice_items']

    def get_invoice_items(self, obj):
        invoice_items = self.context['invoice_items'].filter(product_id=obj.id)
        return InvoiceItemSerializer(invoice_items, many=True).data