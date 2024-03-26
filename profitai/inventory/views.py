from django.shortcuts import get_object_or_404, render
from inventory.models import Product
from invoice.models import InvoiceItem,Invoice
from master_menu.models import ProductType
from rest_framework.views import APIView
from user_profile.models import BusinessProfile
from user_profile.pagination import InfiniteScrollPagination
from .serializers import ProductCreateSerializer, ProductSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q 
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated

class ProductListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def get(self , request):
        business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
        Product.objects.filter(total_quantity__lte=0).update(status=1)
        queryset = business_profile.product_set.all().order_by("product_name")
        total_length_before_pagination = queryset.count()
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request, view=self)
        total_pages = paginator.page.paginator.num_pages
        serializer = ProductSerializer(result_page,many= True)
        if request.query_params.get('type')=="all":
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"All Products Found Successfully!",
                    "data": ProductSerializer(queryset,many= True).data,
    
                }
        else:

            response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"Products Found Successfully!",
                        "total_pages":total_pages,
                        'total_length_all_data' :total_length_before_pagination,
                        "data": serializer.data,
                        "next": paginator.get_next_link()
                    }
        return Response(response)
    def post(self, request):
        # Create a new object
        try:
            business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
            request.data["business_profile"]=business_profile.id
            remaining_quantity = request.data["total_quantity"]
            request.data["remaining_quantity"] = remaining_quantity
            if request.data["remaining_quantity"] <= 0 or request.data["remaining_quantity"] == None:
                request.data["status"]=1
            else:
                request.data["status"]=3
            serializer = ProductCreateSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                
                response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"Product Create Successfully!",
                        "data": serializer.data
                    }
                return Response(response)
            else:
                
                response = {"status_code": 200,
                            "status": "success",
                            "messege": "Product not created "
                            }
                print(serializer.errors)
                return Response(response)
        except Exception as e:
            print(f"error's {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "Internal server error"
            }
            return Response(response)
    
class ProductRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, id):
        return get_object_or_404(Product, id=id)

    def get(self,request,id):
        try:
            instance = self.get_object(id)
            if instance!= None:

                serializer = ProductCreateSerializer(instance)
                response = {
                            "status_code": 200,
                            "status": "success",
                            "message":"Product Found Successfully!",
                            "data": serializer.data
                        }
                return Response(response)
            else:
                response = {"status_code": 200,
                            "status": "success",
                            "messege": "Product dose not exist"}
        except Exception as e:
            print(f"error's {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "Internal server error"
            }
            return Response(response)

    def put(self, request, id):
        # Update an existing object
        try:
            instance = self.get_object(id)
            business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
            request.data["business_profile"]=business_profile.id
            remaining_quantity = request.data["total_quantity"]
            request.data["remaining_quantity"] = remaining_quantity
            if request.data["remaining_quantity"] <= 0 or request.data["remaining_quantity"] == None:
                request.data["status"]=1
            else:
                request.data["status"]=3
            serializer = ProductCreateSerializer(instance, data=request.data)
            if serializer.is_valid():
                serializer.save()
                response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"Product updated Successfully!",
                        "data": serializer.data
                    }
                return Response(response)
            else:
                response = {"status_code": 200,
                                "status": "success",
                                "messege": "Product not updated"}
        except Exception as e:
            print(f"error's {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "Internal server error"
            }
            return Response(response)
    def delete(self, request, id):
        try:
            instance = self.get_object(id)
            instance.delete()
            response = {
                    "status_code": 204,
                    "status": "success",
                    "message": "Product Deleted"
                }
            return Response(response)
        except Exception as e:
            print(f"error's {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": "Internal server error"
            }
            return Response(response)

class InventorySortingFilterAPI(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def post(self, request):
        try:
            sub_queryset = None 
            queryset = None 
            data = None  
            businessprofile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()

            if "sorting" in request.data:
                sorting = request.data["sorting"]
                if sorting == "sale price low to high":
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).order_by('sales_price')
                elif sorting == "sale price high to low":
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).order_by('-sales_price')
                elif sorting == "purchesh price low to high":
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).order_by('purchase_price')
                elif sorting == "purchesh price high to low":
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).order_by('-purchase_price')
                elif sorting == "product name A to Z":
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).order_by('product_name')
                elif sorting == "product name Z to A":
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).order_by('-product_name')
                else:
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).order_by("product_name")
                queryset = sub_queryset
                data = queryset
            elif "Filter" in request.data:
                Filter = request.data["Filter"]
                if Filter == "red":
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).filter(status = 1).order_by("product_name")
                elif Filter == "yellow":
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).filter(status = 2).order_by("product_name")
                elif Filter == "green":
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).filter(status = 3).order_by("product_name")
                elif "category_name" in Filter:
                    product_type_name = Filter["category_name"]
                    sub_queryset = Product.objects.filter(business_profile=businessprofile).filter(product_type__category_name=product_type_name)
                elif Filter == "top 50":
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).annotate(total_quantity_sold=Sum('invoiceitem__quantity')).order_by('-total_quantity_sold')[:50]
                elif Filter == "top 100":
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).annotate(total_quantity_sold=Sum('invoiceitem__quantity')).order_by('-total_quantity_sold')[:100]
                elif Filter == "top 150":
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).annotate(total_quantity_sold=Sum('invoiceitem__quantity')).order_by('-total_quantity_sold')[:150]

                else: 
                    sub_queryset = Product.objects.filter(business_profile = businessprofile).order_by("product_name")
            
                queryset = sub_queryset
                data = queryset
            else:
                data = Product.objects.filter(business_profile = businessprofile).order_by("product_name")

            product_data = data
            total_length_before_pagination = product_data.count()
            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(product_data, request, view=self)
            total_pages = paginator.page.paginator.num_pages
            serializer = ProductSerializer(result_page, many=True)
            response = {
                "status_code": 200,
                "status": "success",
                "message": "Product found Successfully!",
                "data": serializer.data,
                "total_length_before_pagination":total_length_before_pagination,
                "total_pages":total_pages,
                "next": paginator.get_next_link()
            }
            return Response(response)
        except Exception as e:
            print(f"error's {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": f"Internal server error {e}"
            }
            return Response(response)

class InventorySearchAPI(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination

    def get(self,request):
        try:
            businessprofile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
            search_query = request.GET.get('search')
            if search_query !="":
                products = Product.objects.filter(business_profile = businessprofile).filter(
                    Q(product_name__icontains=search_query) |
                    Q(brand__icontains=search_query) |
                    Q(product_type__category_name__icontains = search_query) 
                    
                        )
                if products:
                    product_data = products
                    total_length_before_pagination = product_data.count()
                    paginator = self.pagination_class()
                    result_page = paginator.paginate_queryset(product_data, request, view=self)
                    total_pages = paginator.page.paginator.num_pages
                    serializer = ProductSerializer(result_page, many=True)
                    response = {
                        "status_code": 200,
                        "status": "success",
                        "message": "Product found Successfully!",
                        "total_length_before_pagination":total_length_before_pagination,
                        "total_pages":total_pages,
                        "data": serializer.data,
                        "next": paginator.get_next_link()
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
class InventoryProductQuantityCheckAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            product_id = request.GET.get('product_id')
            quantity = int(request.GET.get('quantity'))
            product = Product.objects.filter(id = product_id).first()
            if product:
                if product.remaining_quantity<quantity:
                    response = {
                                "status_code": 403,
                                "status": "error",
                                "message": "You don't have enough quantity available."
                            }
                else:
                    response = {
                                "status_code": 200,
                                "status": "success",
                               "message": "Product added to the cart successfully."
                            }
                return Response(response)
            else:
                response = {
                                "status_code": 404,
                                "status": "error",
                                 "message": "Product not found."
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
        
class ProductAnalyticsAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        try:
            business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
            if business_profile is not None:
                productss = business_profile.product_set.all()
                invoice = business_profile.invoice_set.all()           
                invoice_item = InvoiceItem.objects.filter(product__in=productss)
                total_reamining_quantity_product = 0 
                if productss.exists():
                    all_remaining_peoduct = productss.aggregate(total_quantity_all_product =Sum("remaining_quantity"))['remaining_quantity']
                    total_reamining_quantity_product = all_remaining_peoduct
                else:
                    total_reamining_quantity_product=total_reamining_quantity_product
                invoice_item_quantity_total = 0 
                for i in invoice_item:
                    if i.invoice in invoice:
                        invoice_item_quantity_total+=i.quantity
                response = {
                    "status_code": 200,
                    "status": "success",
                    "total_sale_product_quantity": invoice_item_quantity_total,
                    "all_remaing_quantity":total_reamining_quantity_product
                }
            else:
                response = {
                    "status_code": 200,
                    "status": "success",
                    "total_sale_product_quantity": 0
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
