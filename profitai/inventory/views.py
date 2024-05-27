from django.shortcuts import get_object_or_404, render
from inventory.models import Product, Batches
from invoice.models import InvoiceItem,Invoice
from master_menu.models import ProductType
from rest_framework.views import APIView
from user_profile.models import BusinessProfile
from user_profile.pagination import InfiniteScrollPagination
from .serializers import ProductCreateSerializer, ProductSerializer, BatchCreateSerializer, BatchUpdateSerializer, BatchSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Prefetch
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

class ProductListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    
    def get(self, request):
               # Get the active business profile for the logged-in user
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()

        if business_profile:
            # Query products associated with the business profile and annotate total_remaining_quantity
            queryset = Product.objects.filter(business_profile=business_profile)\
                .order_by("product_name")\
                .prefetch_related(
                    Prefetch('batches', queryset=Batches.objects.filter(is_deleted=False))
                )\
                .annotate(total_remaining_quantity=Sum('batches__remaining_quantity'))
        else:
            queryset = Product.objects.none()

        # Paginate the queryset
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request, view=self)
        total_pages = paginator.page.paginator.num_pages
        serializer = ProductSerializer(result_page, many=True)

        # Determine response based on 'type' query parameter
        if request.query_params.get('type') == "all":
            response = {
                "status_code": 200,
                "status": "success",
                "message": "All Products Found Successfully!",
                "data": ProductSerializer(queryset, many=True).data,
            }
        else:
            response = {
                "status_code": 200,
                "status": "success",
                "message": "Products Found Successfully!",
                "total_pages": total_pages,
                "data": serializer.data,
                "next": paginator.get_next_link(),
            }

        return Response(response)
    
    
    @transaction.atomic
    def post(self, request):
        try:
            business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
            if not business_profile:
                return Response({"status_code": 400, "status": "error", "message": "Business profile not found"}, status=status.HTTP_400_BAD_REQUEST)

            request.data["business_profile"] = business_profile.id
            product_data = request.data.copy()
            batches_data = product_data.pop('batches', [])

            # Calculate remaining quantity and set status for the product
            remaining_quantity = sum(batch.get('total_quantity', 0) for batch in batches_data)
            product_data["remaining_quantity"] = remaining_quantity
            product_data["status"] = 1 if remaining_quantity <= 0 else 3

            product_serializer = ProductCreateSerializer(data=product_data)
            if product_serializer.is_valid():
                product = product_serializer.save()
                
                batch_errors = []
                for batch_data in batches_data:
                    batch_data['business_profile'] = business_profile.id
                    batch_data['product'] = product.id
                    batch_serializer = BatchCreateSerializer(data=batch_data)
                    if batch_serializer.is_valid():
                        batch_serializer.save()
                    else:
                        batch_errors.append(batch_serializer.errors)
                
                if batch_errors:
                    transaction.set_rollback(True)
                    return Response({"status_code": 400, "status": "error", "message": "Batch creation failed", "errors": batch_errors}, status=status.HTTP_400_BAD_REQUEST)

                response = {
                    "status_code": 200,
                    "status": "success",
                    "message": "Product and Batches created successfully!",
                    "data": product_serializer.data
                }
                return Response(response, status=status.HTTP_200_OK)
            else:
                return Response({"status_code": 400, "status": "error", "message": "Product creation failed", "errors": product_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error: {e}")
            return Response({"status_code": 500, "status": "error", "message": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    
class ProductRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, id):
        return get_object_or_404(Product, id=id)

    def get(self, request, id):
        try:
            instance = self.get_object(id)
            serializer = ProductCreateSerializer(instance)
            response = {
                "status_code": status.HTTP_200_OK,
                "status": "success",
                "message": "Product Found Successfully!",
                "data": serializer.data
            }
            return Response(response)
        except Exception as e:
            print(f"Error: {e}")
            response = {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Internal server error"
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id):
        try:
            instance = self.get_object(id)
            business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
            request.data["business_profile"] = business_profile.id if business_profile else None

            remaining_quantity = request.data.get("total_quantity")
            request.data["remaining_quantity"] = remaining_quantity if remaining_quantity else 0
            request.data["status"] = 1 if remaining_quantity and remaining_quantity <= 0 else 3

            serializer = ProductCreateSerializer(instance, data=request.data)
            if serializer.is_valid():
                serializer.save()
                response_data = {
                    "status_code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Product updated successfully!",
                    "data": serializer.data
                }
                return Response(response_data)
            else:
                response_data = {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Product not updated",
                    "errors": serializer.errors
                }
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error: {e}")
            response_data = {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Internal server error"
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        try:
            instance = self.get_object(id)
            instance.delete()
            response = {
                "status_code": status.HTTP_204_NO_CONTENT,
                "status": "success",
                "message": "Product Deleted"
            }
            return Response(response)
        except Exception as e:
            print(f"Error: {e}")
            response = {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": "error",
                "message": "Internal server error"
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class BatchCreateView(APIView):

    @transaction.atomic
    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            if not product_id:
                return Response({"status_code": 400, "status": "error", "message": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            product = Product.objects.filter(id=product_id).first()
            if not product:
                return Response({"status_code": 400, "status": "error", "message": "Product not found"}, status=status.HTTP_400_BAD_REQUEST)
            
            business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
            if not business_profile:
                return Response({"status_code": 400, "status": "error", "message": "Business profile not found"}, status=status.HTTP_400_BAD_REQUEST)

            batches_data = request.data.get('batches', [])
            if not batches_data:
                return Response({"status_code": 400, "status": "error", "message": "Batches data is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            batch_errors = []
            created_batches = []
            for batch_data in batches_data:
                batch_data['business_profile'] = business_profile.id
                batch_data['product'] = product.id
                batch_serializer = BatchCreateSerializer(data=batch_data)
                if batch_serializer.is_valid():
                    batch = batch_serializer.save()
                    created_batches.append(batch)
                else:
                    batch_errors.append(batch_serializer.errors)

            if batch_errors:
                transaction.set_rollback(True)
                return Response({"status_code": 400, "status": "error", "message": "Batch creation failed", "errors": batch_errors}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"status_code": 200,
                             "status": "success", 
                             "message": "Batches created successfully!", 
                             "data": BatchSerializer(created_batches, many=True).data,
                            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error: {e}")
            return Response({"status_code": 500, "status": "error", "message": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def put(self, request):
        try:
            business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
            batch_id = request.data.get('batch_id')
            product_id = request.data.get('product_id')
            batch_data = request.data.get('batch', {})
            
            batch = Batches.objects.filter(id=batch_id, product__id=product_id, business_profile=business_profile).first()
            if not batch:
                return Response({"status_code": 400, "status": "error", "message": "Batch not found"}, status=status.HTTP_400_BAD_REQUEST)

            batch_serializer = BatchUpdateSerializer(instance=batch, data=batch_data)
            if not batch_serializer.is_valid():
                return Response({"status_code": 400, "status": "error", "message": "Batch update failed", "errors": batch_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            batch = batch_serializer.save()

            response = {
                "status_code": 200,
                "status": "success",
                "message": "Batch updated successfully!",
                "data": batch_serializer.data
            }
            return Response(response, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Error: {e}")
            return Response({"status_code": 500, "status": "error", "message": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       
    @transaction.atomic
    def delete(self, request):
        try:
            # Get the business profile of the current user
            business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
            if not business_profile:
                return Response({"status_code": 400, "status": "error", "message": "Business profile not found"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get batch_id and product_id from request data
            batch_id = request.data.get('batch_id')
            product_id = request.data.get('product_id')

            # Check if batch_id and product_id are provided
            if not batch_id or not product_id:
                return Response({"status_code": 400, "status": "error", "message": "Batch ID and Product ID are required"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Find the batch to delete
            batch = Batches.objects.filter(id=batch_id, product__id=product_id, business_profile=business_profile).first()
            if not batch:
                return Response({"status_code": 400, "status": "error", "message": "Batch not found"}, status=status.HTTP_400_BAD_REQUEST)

            # Delete the batch
            batch.delete()

            # Response after successful deletion
            response = {
                "status_code": 200,
                "status": "success",
                "message": "Batch deleted successfully!"
            }
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error: {e}")
            return Response({"status_code": 500, "status": "error", "message": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
     
class InventorySortingFilterAPI(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination

    def post(self, request):
        try:
            # Get the active business profile for the authenticated user
            businessprofile = BusinessProfile.objects.filter(
                user_profile=request.user, is_active=True, is_deleted=False
            ).first()

            if not businessprofile:
                return Response({
                    "status_code": 400,
                    "status": "error",
                    "message": "Business profile not found"
                }, status=400)

            if businessprofile:
                queryset = Product.objects.filter(business_profile=businessprofile).order_by("product_name").prefetch_related(
                Prefetch('batches', queryset=Batches.objects.filter(is_deleted=False))
            )\
            .annotate(total_remaining_quantity=Sum('batches__remaining_quantity'))
                
            else:
                queryset = Product.objects.none()
            
            sorting = request.data.get("sorting")
            filter_criteria = request.data.get("filter")

            # Apply sorting
            queryset = self.apply_sorting(queryset, sorting)

            # Apply filtering
            queryset = self.apply_filtering(queryset, filter_criteria)
   
            print(queryset)
            total_length_before_pagination = queryset.count()
            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(queryset, request, view=self)
            total_pages = paginator.page.paginator.num_pages
            serializer = ProductSerializer(result_page, many=True)

            return Response({
                "status_code": 200,
                "status": "success",
                "message": "Products found successfully!",
                "data": serializer.data,
                "total_length_before_pagination": total_length_before_pagination,
                "total_pages": total_pages,
                "next": paginator.get_next_link()
            })

        except Exception as e:
            print(f"error: {e}")
            return Response({
                "status_code": 500,
                "status": "error",
                "message": f"Internal server error: {e}"
            }, status=500)

    def apply_sorting(self, queryset, sorting):
        if not sorting:
            return queryset.order_by("product_name")
        
        sorting_map = {
            "sale price low to high": 'batches__sales_price',
            "sale price high to low": '-batches__sales_price',
            "purchase price low to high": 'batches__purchase_price',
            "purchase price high to low": '-batches__purchase_price',
            "product name A to Z": 'product_name',
            "product name Z to A": '-product_name'
        }
        
        sort_field = sorting_map.get(sorting, "product_name")
        return queryset.order_by(sort_field)
    
    
    def apply_filtering(self, queryset, filter_criteria):
        if not filter_criteria:
               return queryset
    
        if filter_criteria == "red":
               queryset = queryset.filter(batches__status=1)
        elif filter_criteria == "yellow":
            queryset = queryset.filter(batches__status=2)
        elif filter_criteria == "green":
            queryset = queryset.filter(batches__status=3)
        elif isinstance(filter_criteria, dict) and "category_name" in filter_criteria:
             queryset = queryset.filter(product_type__category_name=filter_criteria["category_name"])
        elif filter_criteria in ["top 50", "top 100", "top 150"]:
            top_n = int(filter_criteria.split(" ")[1])
            queryset = queryset.annotate(total_quantity_sold=Sum('batches__total_quantity')).order_by('-total_quantity_sold')[:top_n]

        return queryset
    
        
class InventorySearchAPI(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination

    def get(self, request):
        try:
            businessprofile = BusinessProfile.objects.filter(
                user_profile=request.user, is_active=True, is_deleted=False
            ).first()

            if not businessprofile:
                return Response({
                    "status_code": 400,
                    "status": "error",
                    "message": "Business profile not found"
                }, status=400)

            search_query = request.GET.get('search', '')

            if search_query:
                queryset = Product.objects.filter(business_profile=businessprofile).order_by("product_name").prefetch_related(
                      Prefetch('batches', queryset=Batches.objects.filter(is_deleted=False))
                 ).filter(
                    Q(product_name__icontains=search_query) |
                    Q(brand__icontains=search_query) |
                    Q(product_type__category_name__icontains=search_query)
                )

                paginator = self.pagination_class()
                result_page = paginator.paginate_queryset(queryset, request, view=self)
                total_pages = paginator.page.paginator.num_pages
                serializer = ProductCreateSerializer(result_page, many=True)
        
                response = {
                     "status_code": 200,
                     "status": "success",
                     "message": "Products Found Successfully!",
                     "total_pages": total_pages,
                     "data": serializer.data,
                     "next": paginator.get_next_link(),
                 }
                return Response(response)

            else:
                return Response({
                    "status_code": 200,
                    "status": "success",
                    "message": "No search query provided. Please enter a search term."
                }, status=200)

        except Exception as e:
            print(f"error {e}")
            return Response({
                "status_code": 500,
                "status": "error",
                "message": "Internal Server Error."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class InventoryProductQuantityCheckAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            product_id = request.GET.get('product_id')
            batch_number = request.GET.get('batch_number')
            quantity = int(request.GET.get('quantity'))
            # product = Product.objects.filter(id = product_id).first()
            batch = Batches.objects.filter(batch_number=batch_number, product=product_id).first()
            if batch:
                if batch.remaining_quantity and batch.remaining_quantity < quantity:
                    response = {
                                "status_code": 403,
                                "status": "error",
                                "message": "You don't have enough quantity available."
                            }
                    return Response(response)
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
    def get(self, request):
        try:
            business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
            if business_profile:
                productss = business_profile.product_set.all()
                invoice_item = InvoiceItem.objects.filter(product__in=productss)
                
                # Calculate total remaining quantity for all products
                total_remaining_quantity_product = Batches.objects.filter(product__in=productss, is_deleted=False).aggregate(total_remaining=Sum('remaining_quantity'))['total_remaining'] or 0
                
                # Calculate total sale product quantity
                total_sale_product_quantity = invoice_item.aggregate(total_sale_quantity=Sum('quantity'))['total_sale_quantity'] or 0

                response = {
                    "status_code": 200,
                    "status": "success",
                    "total_sale_product_quantity": total_sale_product_quantity,
                    "all_remaining_quantity": total_remaining_quantity_product
                }
            else:
                response = {
                    "status_code": 200,
                    "status": "success",
                    "total_sale_product_quantity": 0,
                    "all_remaining_quantity": 0
                }
            return Response(response)
        except Exception as e:
            print(f"Error: {e}")
            return Response({"status_code": 500, "status": "error", "message": "Internal Server Error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class ProductRecommendListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def get(self, request):
        # Fetch the active business profile for the logged-in user
        business_profile = BusinessProfile.objects.filter(
            user_profile=request.user, 
            is_active=True, 
            is_deleted=False
        ).first()

        # If a business profile exists, fetch the products related to it
        if business_profile:
            # Annotate products with the total quantity remaining in their batches
            queryset = Product.objects.filter(
                business_profile=business_profile
            ).annotate(
                total_remaining_quantity=Sum('batches__remaining_quantity')
            ).filter(
                total_quantity_remaining__isnull=False,
                batches__is_deleted=False
            ).order_by('total_remaining_quantity')

        else:
            # If no business profile is found, return an empty queryset
            queryset = Product.objects.none()

        # Paginate the queryset
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request, view=self)
        total_pages = paginator.page.paginator.num_pages

        # Serialize the paginated queryset
        serializer = ProductSerializer(result_page, many=True)

        # Create the response based on the 'type' query parameter
        if request.query_params.get('type') == "all":
            response = {
                "status_code": 200,
                "status": "success",
                "message": "All Products Found Successfully!",
                "data": ProductSerializer(queryset, many=True).data,
            }
        else:
            response = {
                "status_code": 200,
                "status": "success",
                "message": "Products Found Successfully!",
                "total_pages": total_pages,
                "data": serializer.data,
                "next": paginator.get_next_link(),
            }

        return Response(response)