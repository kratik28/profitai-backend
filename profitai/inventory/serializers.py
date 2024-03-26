from rest_framework import serializers
from master_menu.models import ProductType
from inventory.models import Product
class Product_Type_serilizer(serializers.ModelSerializer):
     class Meta:
        model = ProductType
        fields = ["id","category_name"]

class ProductSerializer(serializers.ModelSerializer):
    product_type = Product_Type_serilizer()
    class Meta:
        model = Product
        fields = ["id","product_name","brand","size","status","total_quantity","remaining_quantity","sales_price","package","add_margin","mrp_price","purchase_price","rate","tax","discount","BAR_code_number","hsn_number","batch_number","product_type","expiry_date","business_profile"]
        

class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"