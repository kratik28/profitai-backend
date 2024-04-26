from rest_framework import serializers
from invoice.models import Invoice
from master_menu.serializers import BusinessTypeSerializer
from user_profile.models import UserProfile, BusinessProfile,Customer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = "__all__"
class UserProfileGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["phone_number","profile_image"]
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.profile_image:
            representation['profile_image'] = self.context['request'].build_absolute_uri(instance.profile_image.url)

        return representation
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["profile_image"]
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.profile_image:
            representation['profile_image'] = self.context['request'].build_absolute_uri(instance.profile_image.url)

        return representation
    
class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        refresh = token
        access = token.access_token
        return {
            'refresh': str(refresh),
            'access': str(access)
        }
        
class BusinessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessProfile
        fields = '__all__'
        
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Exclude certain fields from being required during update
        excluded_fields = ['business_profile']  # Add field names to exclude here
        for field_name in excluded_fields:
            self.fields[field_name].required = False

class InvoiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["invoice_counter", "order_date_time","status","grand_total","remaining_total" ,"tax" ,"discount" ,"payment_type" ,'description',"business_profile" ]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        businessprofile = self.context['request'].user.businessprofile_set.first()
        if instance.business_profile != businessprofile:
            return None
        return representation
    
class InvoiceCustomerSerializer(serializers.ModelSerializer):
     class Meta:
        model = Invoice
        fields = ["grand_total","status"]

    
class CustomerListSerializer(serializers.ModelSerializer):
    invoice_set = InvoiceCustomerSerializer(many=True)
    class Meta:
        model = Customer
        fields = ['id', "customer_name","address" ,"zipcode" ,"phone_number","gst_number" ,"favourite", "email","invoice_set"]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Filter out null values in the invoice_set
        representation['invoice_set'] = [invoice for invoice in representation['invoice_set'] if invoice is not None]

        return representation
class CustomerPdfSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id","customer_name","address","zipcode","phone_number","email","gst_number","is_purchase","favourite"]


class CustomerallSerializer(serializers.ModelSerializer):
    last_invoice_grand_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_invoice_status = serializers.CharField()
    all_remaining =  serializers.DecimalField(max_digits=10, decimal_places=2)
    all_grand_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    all_paid_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    class Meta:
        model = Customer
        fields = ['id', "customer_name","address" ,"zipcode", "is_purchase" ,"phone_number","gst_number" ,"favourite", "email","last_invoice_grand_total","last_invoice_status","all_remaining","all_paid_amount","all_grand_total"]
    
class CustomerSortSerializer(serializers.ModelSerializer):
    last_invoice_grand_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_invoice_status = serializers.CharField()
    all_remaining =  serializers.DecimalField(max_digits=10, decimal_places=2)
    all_grand_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    class Meta:
        model = Customer
        fields = ['id', "customer_name","address" ,"zipcode" ,"phone_number","gst_number" ,"favourite", "email","last_invoice_grand_total","last_invoice_status","all_remaining","all_grand_total"]
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Access request data from the context
        request = self.context.get('request', None)
        if request:
            # Access request data and include it in the response
            typee = request.data.keys()
            data['sort_type'] = list(typee)[0]

        return data