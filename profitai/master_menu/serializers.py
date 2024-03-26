from rest_framework import serializers
from master_menu.models import *

class BusinessTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessType
        fields = '__all__'

class BusinessTypeSerializerList(serializers.ModelSerializer):
    class Meta:
        model = BusinessType
        fields = ['id','business_type','type']

class IndustrySerializerList(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ['id','industry_name','type']

class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = '__all__'

class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = '__all__'

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'

