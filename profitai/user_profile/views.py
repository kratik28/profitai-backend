from django.shortcuts import render
from django.http import Http404, JsonResponse
from invoice.models import Invoice,InvoiceItem
from inventory.models import Product, Batches
from inventory.serializers import ProductCreateSerializer
from invoice.serializers import InvoiceSerializer
from .serializers import TopSellingProductSerializer
from master_menu.serializers import BusinessTypeSerializer, BusinessTypeSerializerList, IndustrySerializerList
from user_profile.models import UserProfile, UserProfileOTP, BusinessProfile, Customer
from user_profile.pagination import InfiniteScrollPagination
from user_profile.serializers import  CustomerListSerializer,VendorListSerializer, VendorCustomerSerializer, CustomerSortSerializer, VendorAllSerializer, CustomerallSerializer, UserProfileGetSerializer, UserProfileUpdateSerializer, UserTokenObtainPairSerializer, BusinessProfileSerializer, CustomerSerializer, VendorSerializer, UserProfileSerializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from telesignenterprise.verify import VerifyClient
from telesign.util import random_with_n_digits
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import random
import datetime
from user_profile.models import UserProfile, Vendor
from master_menu.models import BusinessType, Industry
from rest_framework_simplejwt.tokens import RefreshToken
from master_menu.models import BusinessType
from django.db.models import Sum  ,Count, FloatField , Value    
import indiapins
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from rest_framework.decorators import api_view
from django.db.models import Q,F, ExpressionWrapper, DecimalField, Value, CharField
import requests
from profitai import settings
from django.db.models.functions import TruncDay
import re
from django.db.models.functions import Coalesce
from itertools import chain
from django.core.files.storage import default_storage


def get_grand_total_and_status(customer, businessprofile):
    queryset = customer.annotate(
                        all_remaining=Sum('invoice__remaining_total'),
                        all_grand_total=Sum('invoice__grand_total'),
                        all_paid_amount=Sum('invoice__paid_amount'),
                        last_invoice_grand_total=Subquery(
                            Invoice.objects.filter(business_profile=businessprofile).filter(customer=OuterRef('id')).order_by('-id').values('grand_total')[:1]
                        ),
                        last_invoice_status=Subquery(
                            Invoice.objects.filter(business_profile=businessprofile).filter(customer=OuterRef('id')).order_by('-id').values('status')[:1]
                        )
                    )
    return queryset

def get_vendor_grand_total_and_status(vendor, businessprofile):
    queryset = vendor.annotate(
                        all_remaining=Sum('invoice__remaining_total'),
                        all_grand_total=Sum('invoice__grand_total'),
                        all_paid_amount=Sum('invoice__paid_amount'),
                        last_invoice_grand_total=Subquery(
                            Invoice.objects.filter(business_profile=businessprofile).filter(vendor=OuterRef('id')).order_by('-id').values('grand_total')[:1]
                        ),
                        last_invoice_status=Subquery(
                            Invoice.objects.filter(business_profile=businessprofile).filter(vendor=OuterRef('id')).order_by('-id').values('status')[:1]
                        )
                    )
    return queryset

class CheckPhoneNumberView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        customer_id=settings.TELESIGN_CUSTOMER_ID
        api_key= settings.TELESIGN_API_KEY
        if len(str(phone_number)):
            user = UserProfile.objects.filter(phone_number=phone_number).first()
            if user:
                if user.is_active:
                    otp = random_with_n_digits(6)
                    verify = VerifyClient(customer_id, api_key)
                    response = verify.sms(phone_number, verify_code=otp)
                    if response.ok:
                    # otp = 123456
                    # response = "success"
                    # if response:
                        UserProfileOTP.objects.create(user_profile=user, phone_number=phone_number, otp=otp, is_verified=False)
                        return JsonResponse({'success': 'OTP sent successfully', 'otp': otp}, status=200)
                    else:
                        return JsonResponse({'error': 'Failed to send OTP via TeleSign'}, status=500)
                else:
                    return JsonResponse({'error': 'User is not active'}, status=400)
            else:
                user = UserProfile.objects.create(
                    phone_number=phone_number, is_active=True, username=phone_number)
                if user:
                    if user.is_active:
                        otp = random_with_n_digits(6)
                        verify = VerifyClient(customer_id, api_key)
                        response = verify.sms(phone_number, verify_code=otp)
                        if response.ok:
                        # otp = 123456
                        # response = "success"
                        # if response:
                            UserProfileOTP.objects.create(user_profile=user, phone_number=phone_number, otp=otp, is_verified=False)
                            return JsonResponse({'success': 'OTP sent successfully', 'otp': otp}, status=200)
                        else:
                            return JsonResponse({'error': 'Failed to send OTP via TeleSign'}, status=500)
                    else:
                        return JsonResponse({'error': 'User is not active'}, status=400)
        else:
            return JsonResponse({'message': 'Please Enter Valid phone_number'}, status=400)


class CustomUserOTPLoginView(APIView):
    
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        if phone_number and otp:
            try:
                user = UserProfile.objects.get(phone_number=phone_number)
                authenticated_user = user.validate_otp(user, otp)
                if authenticated_user:
                    # Generate JWT tokens
                    user.last_login = timezone.now()
                    user.save()
                    tokens = UserTokenObtainPairSerializer.get_token(user)

                    business_profile=BusinessProfile.objects.filter(user_profile_id = user.id, is_deleted = False).first()
                    
                    flag = True if business_profile is not None else False
                    if flag==True and business_profile.is_active==True:
            
                        response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"UserProflie Found Successfully!",
                        "token": tokens,
                        "business_profile" : flag,
                        "profile_image": user.profile_image.url if user.profile_image and user.profile_image.url else ""
                        }
                        print(response)
                    elif flag==True and business_profile.is_active==False:
                        response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"your account is deleted by you contact administration!",
                        "is_deleted" : True,
                        "business_profile" :True,
                        "phone number":phone_number
                        }
                    else:
                         response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"UserProflie Found Successfully!",
                        "token": tokens,
                        "business_profile" : flag,
                        "profile_image": ""
                        }
                    return Response(response, status=status.HTTP_200_OK)
                else:
                    return Response({"status_code": 200,
                    "status": "error",
                    "message":"your OTP is invalid!"})
            except UserProfile.DoesNotExist:
                pass

        return Response({'error': 'Invalid OTP or phone_number'}, status=status.HTTP_401_UNAUTHORIZED)

class ProtectedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Your authenticated view logic here
        phone_number = self.request.user.phone_number
        return Response({"status_code": 200,
                         "status": "succses",
                        "message": 'You are authenticated',
                        "phone_number":phone_number}, status=status.HTTP_200_OK)
        

class ProfileImageUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'profile_image' not in request.FILES:
            return Response({"status_code": 400, "status": "error", "message": "No image file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        profile_image = request.FILES['profile_image']
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        
        if not user_profile:
            return Response({"status_code": 404, "status": "error", "message": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        # Delete the previous image if it exists
        if user_profile.profile_image:
            if default_storage.exists(user_profile.profile_image.path):
                default_storage.delete(user_profile.profile_image.path)
                
        request.user.profile_image.save(profile_image.name, ContentFile(profile_image.read()), save=True)

        image_url = request.build_absolute_uri(request.user.profile_image.url)
        return Response({"status_code": 200, "status": "success", "message": "Profile image uploaded successfully", "image_url": image_url}, status=status.HTTP_200_OK)


class BusinessProfileListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
      
        try:
            instance =BusinessProfile.objects.filter(user_profile_id = self.request.user.id,is_active= True, is_deleted = False).first()
            if instance== None:
                # Create a new object
                user_profile = UserProfile.objects.filter(id=self.request.user.id).first()
                request.data['user_profile'] = self.request.user.id   
                if request.data.get('business_type') == 'others':                   
                    businesses = BusinessType.objects.all()
                    BusinessType.objects.get_or_create(type = request.data.get('business_type'),business_type=request.data["new_business"].lower())
                    request.data["business_type"] = businesses.filter(business_type = 'others').last().id
                    request.data["other_business_type"] = businesses.last().id

                elif isinstance(request.data.get('business_type'),int):
                    business_type = BusinessType.objects.filter(id = request.data.get('business_type')).first()
                    request.data["business_type"] = business_type.id
                    request.data["other_business_type"] = None
                else:
                    return Response({"message": "please fill corerct business_type"})

                if request.data.get('industry') == 'others':
                    industries = Industry.objects.all()
                    Industry.objects.get_or_create(type = request.data.get('industry'), industry_name=request.data["new_industry"].lower())
                    request.data["industry"] = industries.filter(industry_name = 'others').last().id
                    request.data["other_industry_type"] = industries.last().id

                elif isinstance(request.data.get('industry'),int):
                    industry_type = Industry.objects.filter(id = request.data.get('industry')).first()
                    request.data["industry"] = industry_type.id
                    request.data["other_industry_type"] = None

                else:
                    return Response({"message": "please fill corerct industry_name"})
                
                userprofileserializer = UserProfileSerializer(user_profile)
                serializer = BusinessProfileSerializer(data=request.data)
                
                if serializer.is_valid():
                    serializer.save()
                    instance =BusinessProfile.objects.filter(user_profile_id = self.request.user,is_active= True, is_deleted = False).first()
                    try:
                        new_business = request.data["new_business"]
                    except:
                        new_business = None
                    try:
                        new_industry = request.data["new_industry"]
                    except:
                        new_industry = None
                    if new_business and new_industry:
                        info = {
                            "business_type_name": BusinessTypeSerializerList(instance.other_business_type,context={"request":request},partial=True).data['business_type'],
                            "industry_type_name": IndustrySerializerList(instance.other_industry_type,context={"request":request},partial=True).data['industry_name']
                        }
                    elif new_business:
                        info = {
                            "business_type_name": BusinessTypeSerializerList(instance.other_business_type,context={"request":request},partial=True).data['business_type'],
                            "industry_type_name": IndustrySerializerList(instance.industry,context={"request":request},partial=True).data['industry_name']
                        }
                    elif new_industry:
                        info = {
                            "business_type_name": BusinessTypeSerializerList(instance.business_type,context={"request":request},partial=True).data['business_type'],
                            "industry_type_name": IndustrySerializerList(instance.other_industry_type,context={"request":request},partial=True).data['industry_name']
                        }
                    else:
                        info = {
                            "business_type_name": BusinessTypeSerializerList(instance.business_type,context={"request":request},partial=True).data['business_type'],
                            "industry_type_name": IndustrySerializerList(instance.industry,context={"request":request},partial=True).data['industry_name']
                    }
                        
                    response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"BusinessProfile Created Successfully!",
                        "data": {**serializer.data,**info},
                        "user_profile_phone":userprofileserializer.data['phone_number'],
                    }
                    return Response(response)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                #objects allready found
                serializer = BusinessProfileSerializer(instance)
                serializer.data["user_profile_phone"] = self.request.user.phone_number
                new_business = instance.other_business_type
                new_industry = instance.other_industry_type
                if new_business and new_industry:
                    info = {
                        "business_type_name": BusinessTypeSerializerList(instance.other_business_type,context={"request":request},partial=True).data['business_type'],
                        "industry_type_name": IndustrySerializerList(instance.other_industry_type,context={"request":request},partial=True).data['industry_name']
                    }
                elif new_business:
                    info = {
                        "business_type_name": BusinessTypeSerializerList(instance.other_business_type,context={"request":request},partial=True).data['business_type'],
                        "industry_type_name": IndustrySerializerList(instance.industry,context={"request":request},partial=True).data['industry_name']
                    }
                elif new_industry:
                    info = {
                        "business_type_name": BusinessTypeSerializerList(instance.business_type,context={"request":request},partial=True).data['business_type'],
                        "industry_type_name": IndustrySerializerList(instance.other_industry_type,context={"request":request},partial=True).data['industry_name']
                    }
                else:
                    info = {
                        "business_type_name": BusinessTypeSerializerList(instance.business_type,context={"request":request},partial=True).data['business_type'],
                        "industry_type_name": IndustrySerializerList(instance.industry,context={"request":request},partial=True).data['industry_name']
                }
                response_instance= {
                        "status_code": 200,
                        "status": "success",
                        "message":"BusinessProfile Found Successfully!",
                        "data": {**serializer.data,**info},
                        "user_profile_data": UserProfileGetSerializer(self.request.user,context={"request":request},partial=True).data
                    }
                return Response(response_instance)
            
        except Exception as e:
            print(f"error {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "Business Profile Not Created."
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)

class BusinessProfileRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, request):
        try:
            businessprofile= BusinessProfile.objects.filter(user_profile = self.request.user, is_active = True, is_deleted = False).first()
            return businessprofile
        except BusinessProfile.DoesNotExist:
            status.HTTP_404_NOT_FOUND

    def get(self, request):
        # Retrieve a single object
        instance = self.get_object(request)
        if instance!= None:
            new_business = instance.other_business_type
            new_industry = instance.other_industry_type
            if new_business and new_industry:
                info = {
                    "business_type_name": BusinessTypeSerializerList(instance.other_business_type,context={"request":request},partial=True).data['business_type'],
                    "industry_type_name": IndustrySerializerList(instance.other_industry_type,context={"request":request},partial=True).data['industry_name']
                }
            elif new_business:
                info = {
                    "business_type_name": BusinessTypeSerializerList(instance.other_business_type,context={"request":request},partial=True).data['business_type'],
                    "industry_type_name": IndustrySerializerList(instance.industry,context={"request":request},partial=True).data['industry_name']
                }
            elif new_industry:
                info = {
                    "business_type_name": BusinessTypeSerializerList(instance.business_type,context={"request":request},partial=True).data['business_type'],
                    "industry_type_name": IndustrySerializerList(instance.other_industry_type,context={"request":request},partial=True).data['industry_name']
                }
            else:
                info = {
                    "business_type_name": BusinessTypeSerializerList(instance.business_type,context={"request":request},partial=True).data['business_type'],
                    "industry_type_name": IndustrySerializerList(instance.industry,context={"request":request},partial=True).data['industry_name']
            }
            serializer = BusinessProfileSerializer(instance)
            response= {
                    "status_code": 200,
                    "status": "success",
                    "message":"BusinessProfile Found Successfully!",
                    "data": {**serializer.data,**info},
                    "user_profile_phone": self.request.user.phone_number
                }
            return Response(response)
        else:
            return Response({"status_code": 200,
                    "status": "error",
                "massage": "please create BusinessProfile"})
        
    def delete(self, request):
        instance = self.get_object(request)
        if instance:
            instance.delete()
            response = {
                    "status_code": 204,
                    "status": "success",
                    "message": "Business Profile Deleted",
                }
        else:
            response = {
                    "status_code": 200,
                    "status": "error",
                    "message":"BusinessProfile Not Found!",
                }
            
        return Response(response)
    
    def put(self, request):
        try:
            instance = self.get_object(request)
            if instance:
                request.data["user_profile"]= self.request.user.id
                request.data["id"] = instance.id

                if request.data.get('business_type') == 'others':
                    business_type_id = BusinessProfile.objects.filter(id=request.data["id"]).last().other_business_type_id
                    businesses = BusinessType.objects.all()
                    Business_instance = businesses.filter(id=business_type_id,type='others').last()
                    if Business_instance:
                        request.data["business_type"] = businesses.filter(business_type = 'others').last().id
                        request.data["other_business_type"] = business_type_id
                        Business_instance.business_type = request.data["new_business"].lower()
                        Business_instance.type = 'others'
                        Business_instance.save()
                    else:
                        BusinessType.objects.get_or_create(type = request.data.get('business_type'),
                            business_type=request.data["new_business"].lower())
                        request.data["business_type"] = businesses.filter(business_type = 'others').last().id
                        request.data["other_business_type"] = businesses.last().id

                elif isinstance(request.data.get('business_type'),int):
                    business_type = BusinessType.objects.filter(id = request.data.get('business_type')).first()
                    request.data["business_type"] = business_type.id
                    request.data["other_business_type"] = None

                else:
                    return Response({"message": "please fill corerct business_type"})
                
                if request.data.get('industry') == 'others':
                    Industry_type_id = BusinessProfile.objects.filter(id=request.data["id"]).last().other_industry_type_id
                    industries = Industry.objects.all()
                    Industry_instance = industries.filter(id=Industry_type_id,type='others').last()
                    if Industry_instance:
                        request.data["industry"] = industries.filter(industry_name = 'others').last().id
                        request.data["other_industry_type"] = Industry_type_id
                        Industry_instance.industry_name = request.data["new_industry"].lower()
                        Industry_instance.type = 'others'
                        Industry_instance.save()
                    else:
                        Industry.objects.get_or_create(type = request.data.get('industry'),
                            industry_name=request.data["new_industry"].lower())
                        request.data["industry"] = industries.filter(industry_name = 'others').last().id
                        request.data["other_industry_type"] = industries.last().id

                elif isinstance(request.data.get('industry'),int):
                    industry_type = Industry.objects.filter(id = request.data.get('industry')).first()
                    request.data["industry"] = industry_type.id
                    request.data["other_industry_type"] = None
                else:
                    return Response({"message": "please fill corerct industry_name"})
                
                serializer = BusinessProfileSerializer(instance, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    try:
                        new_business = request.data["new_business"]
                    except:
                        new_business = None
                    try:
                        new_industry = request.data["new_industry"]
                    except:
                        new_industry = None
                    if new_business and new_industry:
                        info = {
                            "business_type_name": BusinessTypeSerializerList(instance.other_business_type,context={"request":request},partial=True).data['business_type'],
                            "industry_type_name": IndustrySerializerList(instance.other_industry_type,context={"request":request},partial=True).data['industry_name']
                        }
                    elif new_business:
                        info = {
                            "business_type_name": BusinessTypeSerializerList(instance.other_business_type,context={"request":request},partial=True).data['business_type'],
                            "industry_type_name": IndustrySerializerList(instance.industry,context={"request":request},partial=True).data['industry_name']
                        }
                    elif new_industry:
                        info = {
                            "business_type_name": BusinessTypeSerializerList(instance.business_type,context={"request":request},partial=True).data['business_type'],
                            "industry_type_name": IndustrySerializerList(instance.other_industry_type,context={"request":request},partial=True).data['industry_name']
                        }
                    else:
                        info = {
                            "business_type_name": BusinessTypeSerializerList(instance.business_type,context={"request":request},partial=True).data['business_type'],
                            "industry_type_name": IndustrySerializerList(instance.industry,context={"request":request},partial=True).data['industry_name']
                    }
                    
                    response = {
                            "status_code": 200,
                            "status": "success",
                            "message":"BusinessProfile Update Successfully!",
                            "data": {**serializer.data,**info}
                            }
                    return Response(response)
                else:
                    response ={"status_code": 200,
                            "status": "success",
                            "message":"BusinessProfile Update Successfully!",
                            "data": serializer.errors}
                    print(serializer.errors)
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return Response({"status_code": 200,
                            "status": "error",
                            "massage": "please create BusinessProfile"})
        
        except Exception as e:
            print(f"error's {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "BusinessProfile Not update."
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)


class VendorListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination

    def get(self, request):
        name = self.request.GET.get('name', None)
        search = self.request.GET.get('search', None)
        favourite = self.request.GET.get('favourite', None)
        businessprofile = BusinessProfile.objects.filter(user_profile = self.request.user,is_active= True, is_deleted = False).first()
        vendor_queryset = Vendor.objects.filter(business_profile=businessprofile).distinct().order_by('-id')
        if search:
                  vendor_queryset = vendor_queryset.filter( 
                      Q(vendor_name__icontains=search)|
                      Q(phone_number__icontains=search) |
                      Q(gst_number__icontains=search)
                  ).order_by("vendor_name")

        if favourite:
            vendor_queryset = vendor_queryset.filter(favourite= True)
        if name == "ascending":
                vendor_queryset = vendor_queryset.order_by("vendor_name")
        if name == "descending":
                vendor_queryset = vendor_queryset.order_by("-vendor_name")
        
        queryset = get_vendor_grand_total_and_status(vendor_queryset,businessprofile)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request, view=self)
        total_length_before_pagination = queryset.count()
        total_pages = paginator.page.paginator.num_pages
        serializer = VendorAllSerializer(result_page, many=True)
        response = {
            "status_code": 200,
            "status": "success",
            "message": "all purchase vendor found",
            "data": serializer.data,
            "total_length_before_pagination":total_length_before_pagination,
            "total_pages":total_pages,
            "next": paginator.get_next_link(),  # Include the next page link
        }
        return Response(response)

    def post(self, request):
        try:
            phone_number = request.data["phone_number"]
            queryset = Vendor.objects.filter(phone_number=phone_number)
            if queryset.exists():
                data = queryset.first()
                serializer = VendorSerializer(data)
                response={
                    "status_code": 200,
                    "status": "success",
                    "message":"vendor phone number allready exist",
                    "data" : serializer.data
                }
                return Response(response)
            else:
                
                businessprofile=BusinessProfile.objects.filter(user_profile = self.request.user, is_active= True, is_deleted = False).first()
                print(self.request.user, businessprofile)
                request.data["business_profile"] = businessprofile.id
                serializer = VendorSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    response = {
                            "status_code": 200,
                            "status": "success",
                            "message":"vendor created successfully!",
                            "data": serializer.data
                        }
                    return Response(response)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"error's {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "vendor cannot be created."
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            businessprofile=BusinessProfile.objects.filter(user_profile = self.request.user, is_active= True, is_deleted = False).first()
            vendor = Vendor.objects.filter(business_profile=businessprofile, id=request.data['id']).first()
            
            if vendor:
                serializer = VendorSerializer(vendor, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    response = {
                        "status_code": 200,
                        "status": "success",
                        "message": "vendor updated successfully!",
                        "data": serializer.data
                    }
                    return Response(response)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                response = {
                    "status_code": 404,
                    "status": "error",
                    "message": "Vendor not found."
                }
                return Response(response, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            print(f"Error: {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "An error occurred while updating the vendor."
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        try:
            vendor_id = request.data["vendor_id"]
            businessprofile= BusinessProfile.objects.filter(user_profile = self.request.user,is_active= True, is_deleted = False).first()
            vendor = Vendor.objects.filter(id=vendor_id, business_profile=businessprofile).first()
            if vendor:
                vendor.delete()
                response = {
                    "status_code": 200,
                    "status": "success",
                    "message": "Vendor deleted successfully!"
                }
                return Response(response)
            else:
                response = {
                    "status_code": 404,
                    "status": "error",
                    "message": "Vendor not found."
                }
                return Response(response, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"error: {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "An error occurred while trying to delete the customer."
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class CustomerListCreateAPIView(APIView):


    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination

    def get(self, request):
      
        businessprofile=BusinessProfile.objects.filter(user_profile_id = self.request.user.id, is_active= True, is_deleted = False).first()
        cus_queryset = Customer.objects.filter(business_profile=businessprofile).distinct().order_by('-id')
        name = self.request.GET.get('name', None)
        favourite = self.request.GET.get('favourite', None)
        sales = self.request.GET.get('sales', None)
        most_frequent = self.request.GET.get('most_frequent', None)
        most_profitable = self.request.GET.get('most_profitable', None)
        search = self.request.GET.get('search', None)
        debt = self.request.GET.get('debt', None)
        sorted_customers = None
        
      
        
        cus_queryset = cus_queryset.annotate(
            all_remaining=Sum('invoice__remaining_total'),
            all_grand_total=Sum('invoice__grand_total'),
            last_invoice_grand_total=Subquery(
                Invoice.objects.filter(business_profile=businessprofile).filter(customer=OuterRef('id')).order_by('-id').values('grand_total')[:1]
            ),
            last_invoice_status=Subquery(
                Invoice.objects.filter(business_profile=businessprofile).filter(customer=OuterRef('id')).order_by('-id').values('status')[:1]
            )
        )
        cus_queryset = get_grand_total_and_status(cus_queryset,businessprofile)
        if favourite:
            cus_queryset = cus_queryset.filter(favourite= True)
        if name == "ascending":
                cus_queryset = cus_queryset.order_by("customer_name")
        if name == "descending":
                cus_queryset = cus_queryset.order_by("-customer_name")
        if debt == "ascending":
                cus_queryset = cus_queryset.order_by("-remaining_total")
        if debt == "descending":
                cus_queryset = cus_queryset.order_by("remaining_total")
        if sales == "ascending":
                cus_queryset = cus_queryset.order_by("-grand_total")
        if sales == "descending":
                cus_queryset = cus_queryset.order_by("grand_total")
        if most_frequent == "1":
                cus_queryset = cus_queryset.order_by("last_invoice_grand_total")
        if most_profitable == "1":
                cus_queryset = cus_queryset.filter(all_grand_total__gt=0).order_by("-all_grand_total") # cus_queryset.order_by("total_profit")
        if search:
                cus_queryset = cus_queryset.filter( 
                      Q(customer_name__icontains=search)|
                      Q(phone_number__icontains=search) |
                      Q(gst_number__icontains=search)
                  )
    
       
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(cus_queryset, request, view=self)
        total_length_before_pagination = cus_queryset.count()
        total_pages = paginator.page.paginator.num_pages
        serializer = CustomerallSerializer(result_page, many=True)
        response = {
            "status_code": 200,
            "status": "success",
            "message": "all customers found",
            "data": serializer.data,
            "total_length_before_pagination":total_length_before_pagination,
            "total_pages":total_pages,
            "next": paginator.get_next_link(),  # Include the next page link
        }
        return Response(response)
    
    def put(self, request):
        try:
            businessprofile=BusinessProfile.objects.filter(user_profile = self.request.user, is_active= True, is_deleted = False).first()
            customer = Customer.objects.filter(business_profile=businessprofile, id=request.data['id']).first()
            
            if customer:
                serializer = CustomerSerializer(customer, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    response = {
                        "status_code": 200,
                        "status": "success",
                        "message": "Customer updated successfully!",
                        "data": serializer.data
                    }
                    return Response(response)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                response = {
                    "status_code": 404,
                    "status": "error",
                    "message": "Customer not found."
                }
                return Response(response, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            print(f"Error: {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "An error occurred while updating the customer."
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        try:
            phone_number = request.data["phone_number"]
            queryset = Customer.objects.filter(phone_number=phone_number)
            if queryset.exists():
                data = queryset.first()
                serializer = CustomerSerializer(data)
                response={
                    "status_code": 200,
                    "status": "success",
                    "message":"customer phone number allready exist",
                    "data" : serializer.data
                }
                return Response(response)
            else:
                businessprofile=BusinessProfile.objects.filter(user_profile = self.request.user, is_active= True, is_deleted = False).first()
                request.data["business_profile"] = businessprofile.id
                serializer = CustomerSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    response = {
                            "status_code": 200,
                            "status": "success",
                            "message":"customer create Successfully!",
                            "data": serializer.data
                        }
                    return Response(response)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"error's {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "costumer Not create."
            }
            return Response(response, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        try:
            customer_id = request.data["customer_id"]
            businessprofile= BusinessProfile.objects.filter(user_profile = self.request.user,is_active= True, is_deleted = False).first()
            customer = Customer.objects.filter(id=customer_id, business_profile=businessprofile).first()
            if customer:
                customer.delete()
                response = {
                    "status_code": 200,
                    "status": "success",
                    "message": "Customer deleted successfully!"
                }
                return Response(response)
            else:
                response = {
                    "status_code": 404,
                    "status": "error",
                    "message": "Customer not found."
                }
                return Response(response, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"error: {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "An error occurred while trying to delete the customer."
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
             

class CustomerSearchAPI(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def get(self, request):
        try:
            search_query = request.GET.get('search')
            search_type=request.GET.get('type')
            businessprofile=BusinessProfile.objects.filter(user_profile = self.request.user, is_active= True, is_deleted = False).first()
            if search_query !="":
                customers = Customer.objects.filter(
                    Q(customer_name__icontains=search_query) |
                    Q(phone_number__icontains=search_query) |
                    Q(gst_number__icontains=search_query) 
                    
                ).order_by("customer_name")
                if customers and search_type == "global":
                    queryset = get_grand_total_and_status(customers,businessprofile)
                    customer_serializer = CustomerallSerializer(queryset, many=True)
                    response = {
                        "status_code": 200,
                        "status": "success",
                        "message": "Customers are found successfully!",
                        "customers": customer_serializer.data,
                        
                
                    }
                    return Response(response)
                elif customers and search_type == "local":
                    cus_queryset = customers.filter(invoice__business_profile=businessprofile).distinct().order_by('customer_name')

                    queryset = get_grand_total_and_status(cus_queryset,businessprofile)
                    customer_serializer = CustomerallSerializer(queryset, many=True)
                    response = {
                        "status_code": 200,
                        "status": "success",
                        "message": "Customers are found successfully!",
                        "customers": customer_serializer.data,
                    }
                    return Response(response)
                else:
                    msg = f"No results for {search_query}.\n Try checking your spelling or use more general terms"
                    print(msg)
                    response = {
                        "status_code": 200,
                        "status": "success",
                        "message": msg,
                        "customers":[],
                    }
                    return Response(response)
            else:
                msg = f"No results for nonetype{search_query}.\n Try checking your spelling or use more general terms"
                print(msg)
                response = {
                    "status_code": 200,
                    "status": "success",
                    "message": msg,
                }
                return Response(response)



        except Exception as e:
            print(f"error {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "Internal Server Error."
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.core.files.base import ContentFile
import base64
class UserProfileUpdateview(APIView):
    permission_classes = [IsAuthenticated]
    def get(self ,request,*args, **kwargs):
        instance = self.get_object()
        phone_number = self.request.user.phone_number
        businessprofile= BusinessProfile.objects.filter(user_profile = self.request.user, is_active = True, is_deleted = False).first()
        businessprofileserializer = BusinessProfileSerializer(businessprofile)
        serializer = UserProfileGetSerializer(instance,context={"request":request},partial=True)
        response = {
                "status_code": 200,
                "status": "success",
                "message": "UserProfile found",
                "data" :serializer.data,
                "business_profile_data" : businessprofileserializer.data ,  
                "phone_number":phone_number
        }
        return Response(response)
    def put(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            profile_image_uri = request.data['profile_images_uri']  
            if profile_image_uri:
                image_data = profile_image_uri.split(',')[1]
                image_data_decoded = base64.b64decode(image_data)
                profile_image = ContentFile(image_data_decoded, name='profile_image.png')
                instance.profile_image=profile_image
                instance.save()
                serializer = UserProfileUpdateSerializer(instance, context={"request":request},partial=True)
                response_data = {
                        "status_code": 200,
                        "status": "success",
                        "message": "UserProfile Updated",
                        "user_profile_data": serializer.data,
                    }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = {
                    "status_code": 200,
                    "status": "error",
                    "message": "profile image not found"
                }
                return Response(response_data)
        except Exception as e:
            print(e)
            response = {
                "status_code": 200,
                "status": "success",
                "message": f"UserProfile not found {e}"
        }
        return Response(response)

    
    def get_object(self):

        # Retrieve the BusinessProfile object based on the user making the request
        queryset = UserProfile.objects.filter(id=self.self.request.user.id)
        if not queryset.exists():
            raise Http404
        return queryset.first()
    
    
class CustomerfavouriteFrequentTopAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        try:
            businessprofile= BusinessProfile.objects.filter(user_profile = self.request.user, is_active = True, is_deleted = False).first()
            queryset = Customer.objects.filter(invoice__business_profile=businessprofile).distinct().order_by('-id')
            favourite_customer = queryset.filter(favourite= True).order_by('customer_name')
            frequent_customer = queryset.annotate(invoice_count=Count('invoice')).order_by('invoice_count')
            top_customer = queryset.annotate(total_sum=Sum('invoice__grand_total')).order_by('total_sum')    

            favourite_customer_serializer = CustomerSerializer(favourite_customer,many = True)
            frequent_customer_serializer = CustomerSerializer(frequent_customer,many = True)
            top_customer_serializer = CustomerSerializer(top_customer,many = True)

            response   =    {
                            "status_code": 200,
                            "status": "success",
                            "message": "Customer found",
                            "favourite_customer":favourite_customer_serializer.data,
                            "frequent_customer": frequent_customer_serializer.data,
                            "top_customer": top_customer_serializer.data
                           }
            return Response(response)
        except Exception as e:
            print(f"erros {e}")
            return Response({"status_code": 500,
                    "status": "faild",
                    "message": "Customer not found"})

        

class CustomerfavouriteAPI(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def patch(self ,request):
        try:
            id =  request.data.get("id")
            favourite = request.data.get("favourite")
            if not id and not favourite :
                return Response({ "status_code": 200,
                        "status": "success",
                    "message": "Provide either 'favourite' or 'id' in the request data."},
                                status=status.HTTP_400_BAD_REQUEST)

            queryset = Customer.objects.filter(id = id).first()
            if queryset :
                queryset.favourite = favourite
                queryset.save()
                serializer = CustomerListSerializer(queryset)
                response = {
                        "status_code": 200,
                        "status": "success",
                        "message": "UserProfile found",
                        "data" :serializer.data
                }
                return Response(response)
        except Exception as e:
            print(e)
            return Response({"status_code": 500,
                    "status": "faild",
                    "message": "Customer not found"})
            
class VendorFavouriteAPI(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request):
        id = request.data.get("id")
        favourite = request.data.get("favourite")

        if not id or favourite is None:
            return Response({
                "status_code": 400,
                "status": "error",
                "message": "Provide both 'favourite' and 'id' in the request data."
            }, status=status.HTTP_400_BAD_REQUEST)

        vendor = get_object_or_404(Vendor, id=id)
        vendor.favourite = favourite
        vendor.save()

        serializer = VendorListSerializer(vendor)
        response = {
            "status_code": 200,
            "status": "success",
            "message": "Vendor updated successfully",
            "data": serializer.data
        }
        return Response(response)
            
class CustomerFilterAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    
    def get(self,request):
        try:
            favourite = request.GET.get('favourite')
            gst_number = request.GET.get('gst_number')
            area = request.GET.get('area')
            status = request.GET.get('status')
            businessprofile= BusinessProfile.objects.filter(user_profile = self.request.user, is_active = True, is_deleted = False).first()
            
            if not favourite and not gst_number and not status and not area:
                return Response({"status_code": 200,
                            "status": "error",
                    "message": "Provide either 'favourite' or 'gst_number' or status or area in the request data."})
            
            queryset = Customer.objects.filter(invoice__business_profile=businessprofile).distinct().order_by('-id')
            
            paginator = self.pagination_class()
            if favourite == 1 :
                queryset = queryset.filter(favourite = True).order_by("-id")
                customers = get_grand_total_and_status(queryset,businessprofile)
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page,many = True)
            if favourite == 2:
                queryset = queryset.filter(favourite = False).order_by('-id')
                customers = get_grand_total_and_status(queryset,businessprofile)
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page,many = True)
            if gst_number==1:
                queryset = queryset.filter(gst_number__isnull=False)
                customers = get_grand_total_and_status(queryset,businessprofile)
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page,many = True)
            if gst_number==2:
                queryset = queryset.filter(gst_number__isnull=True)
                customers = get_grand_total_and_status(queryset,businessprofile)
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page,many = True)
            if status=="red":
                queryset = get_grand_total_and_status(queryset,businessprofile)
                customers=queryset.filter(last_invoice_status=1).order_by("-id")
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page,many = True)
            if status=="yellow":
                queryset = get_grand_total_and_status(queryset,businessprofile)
                customers=queryset.filter(last_invoice_status=2).order_by("-id")
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page,many = True)
            if status=="green":
                queryset = get_grand_total_and_status(queryset,businessprofile)
                customers=queryset.filter(last_invoice_status=3).order_by("-id")
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page,many = True)
            total_length_before_pagination = customers.count()
            total_pages = paginator.page.paginator.num_pages
            response   =    {
                            "status_code": 200,
                            "status": "success",
                            "message": "Customer found",
                            "data" :customer_serializer.data,
                            "total_length_before_pagination":total_length_before_pagination,
                            "total_pages":total_pages,
                            "next": paginator.get_next_link(), 
                    }
            return Response(response)
        
        except Exception as e:
            print(f"erros {e}")
            return Response({"status_code": 500,
                    "status": "faild",
                    "message": "Customer not found"})


    def post(self , request):
        
        try:
            businessprofile= BusinessProfile.objects.filter(user_profile = self.request.user, is_active = True,  is_deleted = False).first()
            favourite = request.data.get("favourite")
            gst_number = request.data.get("gst_number")
            area = request.data.get("area")
            status = request.data.get("status")
            # if not favourite and not gst_number and not status and not area:
            #     return Response({"status_code": 200,
            #                 "status": "error",
            #         "message": "Provide either 'favourite' or 'gst_number' or status or area in the request data."})
            
            queryset = Customer.objects.filter(invoice__business_profile=businessprofile).distinct().order_by('-id')
            print(queryset, "?>>>>>")
            paginator = self.pagination_class()
            if favourite == 1 :
                customer = queryset.filter(favourite = True).order_by("-id")
                customers = get_grand_total_and_status(customer,businessprofile)
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page, many = True)
            if favourite == 2:
                customer = queryset.filter(favourite = False).order_by('-id')
                customers = get_grand_total_and_status(customer,businessprofile)
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page, many = True)
            if gst_number==1:
                customer = queryset.filter(gst_number__isnull=False)
                customers = get_grand_total_and_status(customer,businessprofile)
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page, many = True)
            if gst_number==2:
                customer = queryset.filter(gst_number__isnull=True)
                customers = get_grand_total_and_status(customer,businessprofile)
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page, many = True)
            if status=="red":
                customer = get_grand_total_and_status(queryset,businessprofile)
                customers=customer.filter(last_invoice_status=1).order_by("-id")
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page, many = True)
            if status=="yellow":
                customer = get_grand_total_and_status(queryset,businessprofile)
                customers=customer.filter(last_invoice_status=2).order_by("-id")
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page, many = True)
            if status=="green":
                customer = get_grand_total_and_status(queryset,businessprofile)
                customers=customer.filter(last_invoice_status=3).order_by("-id")
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page, many = True)
            total_length_before_pagination = customers.count()
            total_pages = paginator.page.paginator.num_pages
            response   =    {
                            "status_code": 200,
                            "status": "success",
                            "message": "Customer found",
                            "data" :customer_serializer.data,
                            "total_length_before_pagination":total_length_before_pagination,
                            "total_pages":total_pages,
                            "next": paginator.get_next_link(), 
                    }
            return Response(response)
        except Exception as e:
            print(e)
            return Response({"status_code": 500,
                    "status": "faild",
                    "message": "Customer not found"})

        
        
class CustomerSortAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def post(self ,request):
        try:
            
            businessprofile = BusinessProfile.objects.filter(user_profile = self.request.user, is_active = True,  is_deleted = False).first()
            # debt = request.data.get("debt")
            # sales = request.data.get("sales")
            # user_name = request.data.get("user_name")
            # most_frequent = request.data.get("most_frequent")
            # most_profitable  = request.data.get("most_profitable") 
            # sorted_customers = None

            queryset = Customer.objects.filter(business_profile=businessprofile)
            queryset = Customer.objects.filter(invoice__business_profile=businessprofile).distinct().order_by('-id')
            paginator = self.pagination_class()
            sorted_customers= queryset
            # customers_with_remaining_total = queryset.annotate(remaining_total=Sum('invoice__remaining_total'))
            # customers_with_total = queryset.annotate(grand_total=Sum('invoice__grand_total'))
            # customers_with_invoice_count = queryset.annotate(invoice_count=Count('invoice'))
            # customers_with_product_profit = queryset.annotate(
            #     total_profit=Sum(ExpressionWrapper(F('invoice__invoiceitem__product__sales_price') - F('invoice__invoiceitem__product__purchase_price'), output_field=DecimalField()))
            #     )
            # if debt == "high to low":
            #     sorted_customers = customers_with_remaining_total.filter(remaining_total__gt=0).order_by('-remaining_total')
            # if debt == "low to high":
            #     sorted_customers = customers_with_remaining_total.filter(remaining_total__gt=0).order_by('remaining_total')
            # if sales == "high to low":
            #     sorted_customers = customers_with_total.filter(grand_total__gt=0).order_by('-grand_total')
            # if sales == "low to high":
            #     sorted_customers = customers_with_total.filter(grand_total__gt=0).order_by('grand_total')
            # if most_frequent:
            #     sorted_customers = customers_with_invoice_count.order_by("invoice_count")
            # if most_profitable:
            #     sorted_customers = customers_with_product_profit.order_by("total_profit")
            # if user_name== "ascending":
            #     sorted_customers = queryset.order_by("customer_name")
            # if user_name =="descending":
            #     sorted_customers = queryset.order_by("-customer_name")
            customers_data = get_grand_total_and_status(sorted_customers, businessprofile)
            total_length_before_pagination = sorted_customers.count()
            result_page = paginator.paginate_queryset(customers_data, request, view=self)
            total_pages = paginator.page.paginator.num_pages
            customer_serializer = CustomerSortSerializer(result_page,many = True,context={'request':request})

            response   =    {
                            "status_code": 200,
                            "status": "success",
                            "message": "customer found",
                            "data" :customer_serializer.data,
                            "total_length_before_pagination":total_length_before_pagination,
                            "total_pages":total_pages,
                            "next": paginator.get_next_link()
                    }
            return Response(response)
        except Exception as e:
            print(f"erros {e}")
            return Response({"status_code": 500,
                    "status": "faild",
                    "message": "Customer not found"})


class BusinessProfileDeactivate(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        try:
            businessprofile = BusinessProfile.objects.filter(user_profile = self.request.user, is_active = True,  is_deleted = False).first()
            print(businessprofile)
            if businessprofile:
                data = request.data['is_active']
                businessprofile.is_active=data
                businessprofile.save()
                return Response({"status_code": 200,
                                "status": "success",
                                "message": "businessprofile deactivate successfully"})
            else:
                return Response({"status_code": 400,
                                "status": "error",
                                "message": "businessprofile not found"})
        except Exception as e:
            return Response({
                        "status_code": 500,
                        "status": "Error",
                        "message": "data not found",
                    })
@api_view(['GET'])  
def get_address_from_zip_code(request, zipcode):
    try:
        if request.method == "GET":
            if len(zipcode) != 6:
                return Response({
                    "status_code": 200,
                    "status": "Error",
                    "message": "Please input a valid pincode",
                })

            addresses = indiapins.matching(zipcode)

            if addresses:
                address = addresses[0]
                name = address["Name"]
                District = address['District']
                State = address['State']

                context = {
                    "status_code": 200,
                    "status": "success",
                    "address2": name,
                    "District": District,
                    "State": State
                }
                return JsonResponse(context)
            else:
                return Response({
                    "status_code": 200,
                    "status": "Error",
                    "message": "Pincode not found",
                })
        else:
            return Response({"status_code": 405,
                            "status": "Error",
                            "message" :"Invalid request method"})

    except Exception as e:
        return Response({
                    "status_code": 500,
                    "status": "Error",
                    "message": "data not found",
                })
class InvoiceSalesReport(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        try:
            businessprofile = BusinessProfile.objects.filter(user_profile = self.request.user, is_active = True,  is_deleted = False).first()
            if businessprofile is not None:
                all_invoice  = businessprofile.invoice_set.all().filter(id=1000)
                paid = all_invoice.filter(payment_type= 'paid')
                pay_letter = all_invoice.filter(payment_type= 'pay_letter')
                remain_payment = all_invoice.filter(payment_type= 'remain_payment')
                all_invoice_count = all_invoice.count()
                paid_invoice_count = paid.count()
                pay_letter_invoice_count = pay_letter.count()
                remain_payment_invoice_count = remain_payment.count()
                response = {
                            "status_code": 200,
                            "status": "success",
                            "all_invoice_count":all_invoice_count,
                            "paid_invoice_count":paid_invoice_count,
                            "pay_letter_invoice_count":pay_letter_invoice_count,
                            "remain_payment_invoice_count":remain_payment_invoice_count,
                            }
            else:
                response = {
                            "status_code": 200,
                            "status": "success",
                            "all_invoice_count":0,
                            "paid_invoice_count":0,
                            "pay_letter_invoice_count":0,
                            "remain_payment_invoice_count":0,
                            }

            return Response(response)
        except Exception as e:
            print(f"error {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "Internal Server Error."
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class AllInvoiceAmountReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self ,request):
        try:
            businessprofile = BusinessProfile.objects.filter(user_profile = self.request.user, is_active = True,  is_deleted = False).first()
            all_invoice  = businessprofile.invoice_set.all()
            grand_total_sum = all_invoice.aggregate(Sum('grand_total'))["grand_total__sum"]
            paid_amount_sum = all_invoice.aggregate(Sum('paid_amount'))['paid_amount__sum']
            if  grand_total_sum and paid_amount_sum is not None:
                remaing_amount = grand_total_sum-paid_amount_sum
                response = {
                    "status_code": 200,
                    "status": "success",
                    "grand_total_sum":grand_total_sum,
                    "paid_amount_sum":paid_amount_sum,
                    "remaing_amount":remaing_amount
                }
            else:
                response = {
                    "status_code": 200,
                    "status": "success",
                    "grand_total_sum":0,
                    "paid_amount_sum":0,
                    "remaing_amount":0
                    }

            return Response(response)
        except Exception as e:
            print(f"error {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "Internal Server Error."
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class GSTVerificationAPIView(APIView):
    def post(self, request):
        api_key = settings.API_KEY
        api_host= settings.API_HOST
        gst_number = request.data.get('gst_number')
        url= "https://gst-return-status.p.rapidapi.com/free/gstin/"+ gst_number
        headers = {
            'Content-Type': 'application/json',
            'X-RapidAPI-Key': api_key,
            'X-RapidAPI-Host': api_host
        }
        verify_response = requests.get(url, headers=headers)
        verify_data = verify_response.json()
        print(verify_data['data'])
        if verify_response.status_code == 200:
            try:
                pattern = r"State - (\w+).*Zone - (\w+)"
                match = re.search(pattern, verify_data['data']['stj'])
               
                response = {
                   'business_name': verify_data['data']['lgnm'],
                   'customer_name': verify_data['data']['lgnm'],
                   'city': match.group(2) if match else "",
                   'state': match.group(1) if match else "",
                   'gstin': verify_data['data']['gstin'],
                   'industry': '',
                   'pan': verify_data['data']['pan'],
                   'nba': verify_data['data']['nba'],
                   'email': '',
                   'address': verify_data['data']['adr'],
                   'address1': verify_data['data']['adr'],
                   'address2': verify_data['data']['stj'],
                   'zipcode': verify_data['data']['pincode']
                }
                return Response(response, status=status.HTTP_200_OK)
            except Exception as e:
                print(f"error {e}")
                response = {
                    "status_code": 500,
                    "status": "error",
                    "message": "GST cannot be fetch."
                }
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                "status_code": 500,
                "status": "Error",
                "message": "data not found",
            }, status=status.HTTP_400_BAD_REQUEST)
       
    
class DashboardAPIView(APIView): 
       permission_classes = [IsAuthenticated]
       def get(self, request):
            # Get the current date and time with microsecond precision
        current_datetime = timezone.now()

        # Calculate the start and end dates of the current and prevoius  month
        current_month_start = current_datetime.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_end = current_month_start.replace(month=current_month_start.month + 1) - datetime.timedelta(microseconds=1)
        previous_month_end = current_month_start - datetime.timedelta(microseconds=1)
        previous_month_start = current_month_start - datetime.timedelta(days=previous_month_end.day)
        
        
        # Get the business profile associated with the current user
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted = False).first()
        
        is_purchase_filter = request.GET.get('is_purchase', 0);
        # Filter invoices by business profile and customer ID
        invoice_data =Invoice.objects.filter(business_profile=business_profile, customer__isnull=False, is_deleted = False)
    
        # Get sales data for the current month
        current_month_data = invoice_data.filter(order_date_time__range=(current_month_start, current_month_end)).annotate(
            day=TruncDay('order_date_time')
        ).values('day').annotate(total=Sum('grand_total')).order_by('day')
        
        previous_month_data = invoice_data.filter(order_date_time__range=(previous_month_start, previous_month_end)).annotate(
            day=TruncDay('order_date_time')
        ).values('day').annotate(total=Sum('grand_total')).order_by('day')


        # Extracting total values for the current month
        current_month_values = [entry['total'] for entry in current_month_data]

        # Extracting total values for the previous month into a dictionary for efficient lookup
        previous_month_totals = {entry['day'].strftime('%d %b %Y'): entry['total'] for entry in previous_month_data}

        # Initialize previous month values list
        previous_month_values = []

       # Generating labels for each day in the current month
        x_labels = []

        for entry in current_month_data:
          day_str = entry['day'].strftime('%d %b %Y')
          x_labels.append(day_str)  # Add label for current month
          previous_month_total = previous_month_totals.get(day_str, 0)  # Get total for corresponding day in previous month
          previous_month_values.append(previous_month_total)

           # If the day in the current month doesn't have a corresponding entry in the previous month, add it with a value of 0
          if day_str not in previous_month_totals:
            previous_month_totals[day_str] = 0

        # Now, synchronize previous month values to match the length of current month values
        for day_str, previous_month_total in previous_month_totals.items():
           if day_str not in x_labels:
              x_labels.append(day_str)  # Add label for previous month
              current_month_values.append(0)  # Add 0 to current month values
              previous_month_values.append(previous_month_total)  # Add total for previous month

        # Sort x_labels to ensure chronological order
        x_labels.sort()
       
        products_data = Product.objects.filter(business_profile=business_profile)

        # Calculate total sales by brand
        total_sales_by_brand = Batches.objects.filter(business_profile=business_profile).values('product__brand').annotate(
            value=Sum(
                ExpressionWrapper(
                    F('sales_price') * F('remaining_quantity'),
                    output_field=DecimalField()
                )
            )
        )
        
        # Calculate the total debit
        total_debit = invoice_data.filter(
            payment_type__in=["pay_later", "remain_payment"]
        ).aggregate(
                total_debit=Sum(
                ExpressionWrapper(
                    F('sub_total') - F('paid_amount'),
                    output_field=DecimalField()
                )
            )
        )
        
        today = current_datetime.date()
        
        today_sales = invoice_data.filter(order_date_time__date=today).aggregate(total_cash=Sum('sub_total'))
        cash_in_hand = invoice_data.aggregate(total_cash=Sum('paid_amount'))
       
        # Calculate total stock price
        stock_total = Batches.objects.filter(business_profile=business_profile).aggregate(
            total_stock_price=Sum(
                ExpressionWrapper(
                    F('sales_price') * F('remaining_quantity'),
                    output_field=DecimalField()
                )
            ),
            stock_profit_margin=Sum(
                ExpressionWrapper(
                    (F('sales_price')-F('purchase_price')) * F('remaining_quantity'),
                    output_field=FloatField()
                )
            )
        )

        # Aggregate invoice data
        total_sales_prices = invoice_data.aggregate(total=Sum('sub_total'))['total']
        
        invoice_ids = invoice_data.values_list('id', flat=True)
        total_sales_product_price = InvoiceItem.objects.filter(invoice_id__in=invoice_ids).aggregate(
        total_sales_product_price=Sum(
            ExpressionWrapper(
                F('batch__purchase_price') * F('quantity'),
                output_field=DecimalField()
            )
          )
        )['total_sales_product_price']



        # Get the current month
        current_month = timezone.now().month

        # Fetch top selling product IDs
        top_selling_products = InvoiceItem.objects.filter(
            invoice__created_at__month=current_month
        ).values('product_id').annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:10]
        

        # Extract product IDs and quantities
        top_selling_product_ids = [item['product_id'] for item in top_selling_products]
        product_quantities = {item['product_id']: item['total_quantity'] for item in top_selling_products}

        # Get the sales price of the first related batch and specify the output_field as FloatField
        batches_sales_price = Batches.objects.filter(
            product_id=OuterRef('pk')
        ).values('sales_price')[:1]

        # Fetch the top selling products with annotated sales price
        top_selling_items = products_data.filter(id__in=top_selling_product_ids).annotate(
            name=F('product_name'),  # Rename product_name as name
            amount=Coalesce(Subquery(batches_sales_price, output_field=FloatField()), Value(0.0), output_field=FloatField())  # Use Coalesce to handle cases where there's no related batch
        ).distinct()
        
        # Prepare the final list of top selling items
        top_selling_items_list = [
        {
           "id": item.id,
           "name": item.name,
           "amount": item.amount,
           "total_selling_quantity": product_quantities[item.id]
        }
        for item in top_selling_items
        ]

        # Extract the total values
        cash_in_hand_value = cash_in_hand['total_cash'] or 0
        total_debit_value = total_debit['total_debit'] or 0
        today_sales_value = today_sales['total_cash'] or 0
        total_sales_price = float(total_sales_prices or 0)
        total_sales_product_price = float(total_sales_product_price or 0)
        absolute_profit_margin = (total_sales_price - total_sales_product_price)
        expected_absolute_profit_margin = (stock_total["stock_profit_margin"] + absolute_profit_margin) or 0
        
        response = {
            "status_code": 200,
            "status": "success",
            "message": "Invoice data retrieved successfully!",
            'data': {
                'today_target_sales': {
                    'today_sales_value': today_sales_value,
                    'target_sales_value': 250000
                },
                'top_selling_products': top_selling_products,
                'top_selling_items': top_selling_items_list,
                'total_sales_by_brand': total_sales_by_brand,
                'sales_graph': {
                   'current_month_data': current_month_values,
                   'current_month': current_month_values,
                   'previous_month_data': previous_month_values,
                   'x_labels': x_labels
                },
               'profit_margin': 0.0 if total_sales_price == 0 else (absolute_profit_margin / total_sales_price) * 100,
               'absolute_profit_margin': absolute_profit_margin,
               'total_sales_price': (total_sales_prices or 0.0),
               'total_debit_value': total_debit_value,
               'cash_in_hand_value': cash_in_hand_value,
               'today_sales_value': today_sales_value,
               'total_stock_price': stock_total['total_stock_price'] or 0,
               'expected_absolute_profit_margin': expected_absolute_profit_margin, # total sales profit + upcoming sales profit (after deducting purchases)
               'expected_profit_margin': (expected_absolute_profit_margin / (total_sales_price+float(stock_total['total_stock_price']))) * 100, 
            }
        }

        return Response(response)

class UserProfitDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request):
        # Delete active BusinessProfile associated with the current user
        deleted_count = BusinessProfile.objects.filter(user_profile=self.request.user, is_active=True,  is_deleted = False).update( is_deleted = True)
        print(deleted_count)
        if deleted_count > 0:  # If at least one BusinessProfile was successfully deactivated
            response_data = {
                "status_code": status.HTTP_200_OK,
                "status": "success",
                "message": "Account deleted successfully!"
            }
        else:  # If no BusinessProfile was found or deleted
            response_data = {
                "status_code": status.HTTP_404_NOT_FOUND,
                "status": "error",
                "message": "No active account found to delete"
            }
        
        return Response(response_data, status=response_data["status_code"])
    

class GlobalSearchAPIView(APIView):
    def get(self, request):
        query = request.query_params.get('query', '')

        if not query:
            return Response({
                "status_code": 400,
                "status": "failure",
                "message": "Query parameter is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the active business profile for the current user
        business_profile = BusinessProfile.objects.filter(
            user_profile=request.user, 
            is_active=True, 
            is_deleted=False
        ).first()

        if not business_profile:
            return Response({
                "status_code": 404,
                "status": "failure",
                "message": "No active business profile found for the user."
            }, status=status.HTTP_404_NOT_FOUND)

        # Search Products by name or brand within the business profile
        products = Product.objects.filter(
            Q(product_name__icontains=query) | Q(brand__icontains=query),
            business_profile=business_profile
        )
        product_serializer = ProductCreateSerializer(products, many=True)
        
        # Search Customers (including Vendors) by name or phone number within the business profile
        customers_data = Customer.objects.filter(
           Q(customer_name__icontains=query) | Q(phone_number__icontains=query),
           business_profile=business_profile
        )
        
        vendors_data = Vendor.objects.filter(
           Q(vendor_name__icontains=query) | Q(phone_number__icontains=query),
           business_profile=business_profile
        )

        response = {
            "status_code": 200,
            "status": "success",
            "message": "Search results retrieved successfully.",
            "data": {
                "products": product_serializer.data,
                "customers": CustomerSerializer(customers_data, many=True).data,
                "vendors": VendorSerializer(vendors_data, many=True).data
            }
        }

        return Response(response)
    
    
class VendorCustomerListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination  # Assuming you have this pagination class implemented

    def get(self, request):
        name = request.GET.get('name', None)
        search = request.GET.get('search', None)
        favourite = request.GET.get('favourite', None)
        customer_only = request.GET.get('customer_only', None) == 'true'
        vendor_only = request.GET.get('vendor_only', None) == 'true'
        
        businessprofile = BusinessProfile.objects.filter(
            user_profile=request.user,
            is_active=True, 
            is_deleted=False
        ).first()

        if not businessprofile:
            return Response({"status": "error", "message": "Business profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Initialize the combined_queryset
        combined_queryset = []

        if customer_only:
            customer_filters = Q(business_profile=businessprofile, is_active=True)
            if search:
                customer_filters &= Q(customer_name__icontains=search) | Q(phone_number__icontains=search) | Q(gst_number__icontains=search)
            if favourite:
                customer_filters &= Q(favourite=True)
            customer_queryset = Customer.objects.filter(customer_filters).annotate(
                name=F('customer_name'),
                type=Value('customer', output_field=CharField())
            )
            combined_queryset = list(customer_queryset)
        
        elif vendor_only:
            vendor_filters = Q(business_profile=businessprofile, is_active=True)
            if search:
                vendor_filters &= Q(vendor_name__icontains=search) | Q(phone_number__icontains=search) | Q(gst_number__icontains=search)
            if favourite:
                vendor_filters &= Q(favourite=True)
            vendor_queryset = Vendor.objects.filter(vendor_filters).annotate(
                name=F('vendor_name'),
                type=Value('vendor', output_field=CharField())
            )
            combined_queryset = list(vendor_queryset)
        
        else:
            vendor_filters = Q(business_profile=businessprofile, is_active=True)
            customer_filters = Q(business_profile=businessprofile, is_active=True)
            if search:
                vendor_filters &= Q(vendor_name__icontains=search) | Q(phone_number__icontains=search) | Q(gst_number__icontains=search)
                customer_filters &= Q(customer_name__icontains=search) | Q(phone_number__icontains=search) | Q(gst_number__icontains=search)
            if favourite:
                vendor_filters &= Q(favourite=True)
                customer_filters &= Q(favourite=True)
            vendor_queryset = Vendor.objects.filter(vendor_filters).annotate(
                name=F('vendor_name'),
                type=Value('vendor', output_field=CharField())
            )
            customer_queryset = Customer.objects.filter(customer_filters).annotate(
                name=F('customer_name'),
                type=Value('customer', output_field=CharField())
            )
            combined_queryset = list(chain(vendor_queryset, customer_queryset))

        # Apply sorting
        reverse = (name == 'descending')
        combined_queryset.sort(key=lambda x: x.name, reverse=reverse)

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(combined_queryset, request, view=self)
        total_length_before_pagination = len(combined_queryset)
        total_pages = (total_length_before_pagination // paginator.page_size) + (1 if total_length_before_pagination % paginator.page_size > 0 else 0)
        serializer = VendorCustomerSerializer(result_page, many=True)

        response = {
            "status_code": 200,
            "status": "success",
            "message": "All vendors and customers found",
            "data": serializer.data,
            "total_length_before_pagination": total_length_before_pagination,
            "total_pages": total_pages,
            "next": paginator.get_next_link(),
        }
        return Response(response)