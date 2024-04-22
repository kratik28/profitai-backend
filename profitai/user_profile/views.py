from django.shortcuts import render
from django.http import Http404, JsonResponse
from invoice.models import Invoice
from invoice.serializers import InvoiceSerializer
from master_menu.serializers import BusinessTypeSerializer, BusinessTypeSerializerList, IndustrySerializerList
from user_profile.models import UserProfile, UserProfileOTP, BusinessProfile, Customer
from user_profile.pagination import InfiniteScrollPagination
from user_profile.serializers import  CustomerListSerializer, CustomerSortSerializer, CustomerallSerializer, UserProfileGetSerializer, UserProfileUpdateSerializer, UserTokenObtainPairSerializer, BusinessProfileSerializer, CustomerSerializer, UserProfileSerializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from telesignenterprise.verify import VerifyClient
from telesign.util import random_with_n_digits
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import random
from datetime import datetime
from user_profile.models import UserProfile
from master_menu.models import BusinessType, Industry
from rest_framework_simplejwt.tokens import RefreshToken
from master_menu.models import BusinessType
from django.db.models import Sum  ,Count     
import indiapins
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from rest_framework.decorators import api_view
from django.db.models import Q,F, ExpressionWrapper, DecimalField
import requests
from profitai import settings

def get_grand_total_and_status(customer,businessprofile):
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
                    query = UserProfile.objects.get(phone_number=phone_number)

                    tokens = UserTokenObtainPairSerializer.get_token(user)
                    Dataserializer = UserProfileSerializer(query)

                    business_profile=BusinessProfile.objects.filter(user_profile_id = user.id).first()
                    flag = True if business_profile is not None else False
                    if flag==True and business_profile.is_active==True:
            
                        response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"UserProflie Found Successfully!",
                        "token": tokens,
                        "business_profile" : flag
                        }
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
                        "business_profile" : flag
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
        phone_number = request.user.phone_number
        return Response({"status_code": 200,
                         "status": "succses",
                        "message": 'You are authenticated',
                        "phone_number":phone_number}, status=status.HTTP_200_OK)


class BusinessProfileListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
      
        try:
            instance =BusinessProfile.objects.filter(user_profile_id = request.user.id,is_active= True).first()
            if instance== None:
                # Create a new object
                user_profile = UserProfile.objects.filter(id=request.user.id).first()
                request.data['user_profile'] = request.user.id   
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
                    instance =BusinessProfile.objects.filter(user_profile_id = request.user,is_active= True).first()
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
                serializer.data["user_profile_phone"] = request.user.phone_number
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
                        "user_profile_data": UserProfileGetSerializer(request.user,context={"request":request},partial=True).data
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
            businessprofile= BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
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
                    "user_profile_phone": request.user.phone_number
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
                request.data["user_profile"]= request.user.id
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
        businessprofile=BusinessProfile.objects.filter(user_profile = request.user,is_active= True).first()
        vendor_queryset = Customer.objects.filter(invoice__business_profile=businessprofile, is_purchase=True).distinct().order_by('-id')
        if search:
                  vendor_queryset = vendor_queryset.filter( 
                      Q(customer_name__icontains=search)|
                      Q(phone_number__icontains=search) |
                      Q(gst_number__icontains=search)
                  ).order_by("customer_name")

        if name == "ascending":
                vendor_queryset = vendor_queryset.order_by("customer_name")
        if name == "descending":
                vendor_queryset = vendor_queryset.order_by("-customer_name")
        
        queryset = get_grand_total_and_status(vendor_queryset,businessprofile)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request, view=self)
        total_length_before_pagination = queryset.count()
        total_pages = paginator.page.paginator.num_pages
        serializer = CustomerallSerializer(result_page, many=True)
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
    

class CustomerListCreateAPIView(APIView):


    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination

    def get(self, request):
        businessprofile=BusinessProfile.objects.filter(user_profile = request.user,is_active= True).first()
        
        cus_queryset = Customer.objects.filter(invoice__business_profile=businessprofile,is_purchase=False).distinct().order_by('-id')
        
        name = self.request.GET.get('name', None)
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
                cus_queryset = cus_queryset.order_by("total_profit")
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
                businessprofile=BusinessProfile.objects.filter(user_profile = request.user,is_active= True).first()
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

class CustomerSearchAPI(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def get(self, request):
        try:
            search_query = request.GET.get('search')
            search_type=request.GET.get('type')
            businessprofile=BusinessProfile.objects.filter(user_profile = request.user,is_active= True).first()
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
        phone_number = request.user.phone_number
        businessprofile= BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
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
        queryset = UserProfile.objects.filter(id=self.request.user.id)
        if not queryset.exists():
            raise Http404
        return queryset.first()
class CustomerfavouriteFrequentTopAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        try:
            businessprofile= BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
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
class CustomerFilterAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    
    def get(self,request):
        try:
            favourite = request.GET.get('favourite')
            gst_number = request.GET.get('gst_number')
            area = request.GET.get('area')
            status = request.GET.get('status')
            businessprofile= BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
            
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
            businessprofile= BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
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
                customer_serializer = CustomerallSerializer(result_page,many = True)
            if favourite == 2:
                customer = queryset.filter(favourite = False).order_by('-id')
                customers = get_grand_total_and_status(customer,businessprofile)
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page,many = True)
            if gst_number==1:
                customer = queryset.filter(gst_number__isnull=False)
                customers = get_grand_total_and_status(customer,businessprofile)
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page,many = True)
            if gst_number==2:
                customer = queryset.filter(gst_number__isnull=True)
                customers = get_grand_total_and_status(customer,businessprofile)
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page,many = True)
            if status=="red":
                customer = get_grand_total_and_status(queryset,businessprofile)
                customers=customer.filter(last_invoice_status=1).order_by("-id")
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page,many = True)
            if status=="yellow":
                customer = get_grand_total_and_status(queryset,businessprofile)
                customers=customer.filter(last_invoice_status=2).order_by("-id")
                result_page = paginator.paginate_queryset(customers, request, view=self)
                customer_serializer = CustomerallSerializer(result_page,many = True)
            if status=="green":
                customer = get_grand_total_and_status(queryset,businessprofile)
                customers=customer.filter(last_invoice_status=3).order_by("-id")
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
            print(e)
            return Response({"status_code": 500,
                    "status": "faild",
                    "message": "Customer not found"})

        
        
class CustomerSortAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def post(self ,request):
        try:
            
            businessprofile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
            # debt = request.data.get("debt")
            # sales = request.data.get("sales")
            # user_name = request.data.get("user_name")
            # most_frequent = request.data.get("most_frequent")
            # most_profitable  = request.data.get("most_profitable") 
            # sorted_customers = None

            queryset = Customer.objects.filter(business_profile=businessprofile)
            queryset = Customer.objects.filter(invoice__business_profile=businessprofile,is_purchase=False).distinct().order_by('-id')
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
            customers_data = get_grand_total_and_status(sorted_customers,businessprofile)
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
            businessprofile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
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
            businessprofile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
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
            businessprofile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
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
        api_secret = settings.API_SECRET
        # auth_url = "https://test-api.sandbox.co.in/authenticate"
        auth_url= "https://api.sandbox.co.in/authenticate"
        auth_headers = {
            "x-api-key": api_key,
            "x-api-secret": api_secret,
            "x-api-version": "1.0"
        }
        auth_response = requests.post(auth_url, headers=auth_headers)
        auth_data = auth_response.json()
       
        if auth_response.status_code == 200:
            access_token = auth_data.get("access_token")
            gst_number = request.data.get('gst_number')
            # verify_url = f"https://test-api.sandbox.co.in/gsp/public/gstin/{gst_number}"
            verify_url = f"https://api.sandbox.co.in/gsp/public/gstin/{gst_number}"
            headers = {
                "Authorization": access_token,
                "x-api-key": api_key,
                "x-api-version": "1.0"
            }

            verify_response = requests.get(verify_url, headers=headers)
            verify_data = verify_response.json()

            if verify_response.status_code == 200:
                try:
                    business_name = verify_data['data']['tradeNam']
                    gstin = verify_data['data']['gstin']
                    state = verify_data['data']['pradr']['addr']['stcd']
                    industry_type = verify_data['data']['nba'][0]
                    name = verify_data['data']['lgnm']
                    # Extracting primary address
                    pradr_add = verify_data['data']['pradr']['addr']
                    primary_add_parts = [pradr_add.get('bnm', ''), pradr_add.get('bno', ''), pradr_add.get('st', ''), pradr_add.get('loc', '')]
                    primary_address = ' '.join(part for part in primary_add_parts if part)
                    primary_zip_code = pradr_add['pncd']
                    primary_landmark = pradr_add.get('landMark', '')
                    primary_business_type = verify_data['data']['pradr'].get('ntr', '')
                    city=pradr_add['dst']
                    adadr_list = verify_data['data']['adadr']
                    if adadr_list:
                        current_add = adadr_list[0]['addr']
                        current_add_parts = [current_add.get('bnm', ''), current_add.get('bno', ''), current_add.get('st', ''), current_add.get('loc', '')]
                        current_address = ' '.join(part for part in current_add_parts if part)
                        current_zip_code = current_add['pncd']
                        current_landmark = current_add.get('landMark', '')
                        current_business_type =adadr_list[0]['ntr']
                    else:
                        current_address = ""
                        current_zip_code = ""
                        current_landmark = ""
                        current_business_type = ""
                except KeyError as e:
                    print(f'error,{e}')
                    business_name = ''
                    name='',
                    city='',
                    gstin = ''
                    state = ''
                    industry_type = ''
                    primary_address = ''
                    primary_zip_code = ''
                    primary_landmark = ''
                    primary_business_type = ''

                response_data = {
                    "business_name": business_name,
                    "name":name,
                    "gstin": gstin,
                    "city":city,
                    "industry_type": industry_type,
                    "state": state,
                    "email_id": "",
                    "mob_number":"",
                    "primary_add_data": {
                    "primary_address_line_1": primary_address,
                    "primary_address_line_2": primary_landmark,
                    "primary_business_type": primary_business_type,
                    "primary_zip_code": primary_zip_code
                    }
                    ,"current_add_data":{
                    "current_address_line_1": current_address,
                    "current_address_line_2": current_landmark,
                    "current_business_type": current_business_type,
                    "current_zip_code": current_zip_code,
                    }
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status_code": 500,
                    "status": "Error",
                    "message": "data not found",
                }, status=status.HTTP_400_BAD_REQUEST)