from rest_framework import serializers
from .models import RequestInvoice, RequestInvoiceProduct

class RequestInvoiceProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestInvoiceProduct
        fields = '__all__'

class RequestInvoiceSerializer(serializers.ModelSerializer):
    products = RequestInvoiceProductSerializer(many=True, read_only=True)

    class Meta:
        model = RequestInvoice
        fields = '__all__'
