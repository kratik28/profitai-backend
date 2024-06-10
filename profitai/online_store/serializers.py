from rest_framework import serializers
from .models import BusinessInventoryLink
from inventory.models import Product
from inventory.serializers import ProductCreateSerializer

class BusinessInventoryLinkSerializer(serializers.ModelSerializer):
    products = ProductCreateSerializer(many=True, read_only=True)
    product_ids = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), many=True, write_only=True)

    class Meta:
        model = BusinessInventoryLink
        fields = ['id', 'unique_link_code', 'products', 'product_ids', 'created_at', 'updated_at']
        read_only_fields = ['unique_link_code']

    def create(self, validated_data):
        products = validated_data.pop('product_ids')
        link = BusinessInventoryLink.objects.create(**validated_data)
        link.products.set(products)
        return link

    def update(self, instance, validated_data):
        products = validated_data.pop('product_ids', None)
        instance = super().update(instance, validated_data)
        if products is not None:
            instance.products.set(products)
        return instance