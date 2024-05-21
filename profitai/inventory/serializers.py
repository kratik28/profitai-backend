from rest_framework import serializers
from master_menu.models import ProductType
from inventory.models import Product, Batches


class Product_Type_serilizer(serializers.ModelSerializer):
     class Meta:
        model = ProductType
        fields = ["id","category_name"]

class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batches
        fields = ["id", "size", "total_quantity", "remaining_quantity", "sales_price", "mrp_price", "rate", 
                  "purchase_price", "tax", "discount", "add_margin", "status", "bar_code_number", 
                  "hsn_number", "batch_number", "package", "expiry_date", "is_deleted"]
        
class BatchCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batches
        fields = '__all__'

class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ["id", "name"]  # Adjust fields according to your ProductType model

class ProductSerializer(serializers.ModelSerializer):
    # product_type = ProductTypeSerializer()
    batches = BatchSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "product_name", "brand", "product_type", "business_profile", "batches"]


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"