from django.shortcuts import get_object_or_404
from invoice.utils import get_barchart, get_percentage, invoice_pdf_create, page_break, set_remaining_product_quantity, update_pdf
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from inventory.models import Product, Batches
from inventory.serializers import ProductSerializer
from invoice.serializers import InvoiceCreateSerializer, InvoiceSerializer,InvoiceItemSerializer, ProductdataSerializer
from invoice.models import Invoice,InvoiceItem
from rest_framework.permissions import IsAuthenticated
from user_profile.models import BusinessProfile, Customer, Vendor
from datetime import datetime
from django.db.models import Q, Prefetch
from user_profile.pagination import InfiniteScrollPagination
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone
import datetime
from rest_framework.exceptions import ValidationError

class InvoiceCustomerListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def get(self , request):
        customerId = request.GET.get("customer_id")
        is_cancelled = request.GET.get("is_cancelled", "0") == "1"
        
        business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True, is_deleted = False).first()
        queryset = Invoice.objects.filter(business_profile=business_profile,vendor__isnull = True, is_deleted = is_cancelled)
        if customerId:
            queryset = queryset.filter(customer__id = customerId).order_by('-id')
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request, view=self)
        total_length_before_pagination = queryset.count()
        total_pages = paginator.page.paginator.num_pages
        current_domain = request.build_absolute_uri('/media').rstrip('/')
        serializer = InvoiceCreateSerializer(result_page,context={"request":request,'current_domain': current_domain},many= True)
        if request.query_params.get("type")=="all":
            response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"Invoice Found Successfully!",
                        "data": InvoiceCreateSerializer(queryset,context={'current_domain': current_domain},many= True).data,}
        else:
            response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"Invoice Found Successfully!",
                        "data": serializer.data,
                        "total_pages":total_pages,
                        "total_length_before_pagination":total_length_before_pagination,
                        "next": paginator.get_next_link(),  # Include the next page link
            }
        return Response(response)   
    
class InvoiceVendorListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def get(self , request):
        vendorId = request.GET.get("vendor_id")
        is_cancelled = request.GET.get("is_cancelled", "0") == "1"
        business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True, is_deleted = False).first()
        queryset = Invoice.objects.filter(business_profile=business_profile, customer__isnull = True, is_deleted = is_cancelled).order_by('-id')
        if vendorId:
            queryset = queryset.filter(vendor__id = vendorId).order_by('-id')
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request, view=self)
        total_length_before_pagination = queryset.count()
        total_pages = paginator.page.paginator.num_pages
        current_domain = request.build_absolute_uri('/media').rstrip('/')
        serializer = InvoiceCreateSerializer(result_page,context={"request":request,'current_domain': current_domain},many= True)
        if request.query_params.get("type")=="all":
            response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"Invoice Found Successfully!",
                        "data": InvoiceCreateSerializer(queryset,context={'current_domain': current_domain},many= True).data,}
        else:
            response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"Invoice Found Successfully!",
                        "data": serializer.data,
                        "total_pages":total_pages,
                        "total_length_before_pagination":total_length_before_pagination,
                        "next": paginator.get_next_link(),  # Include the next page link
            }
        return Response(response)   

class InvoiceListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def get(self , request):
        is_purchase_filter = request.GET.get('is_purchase', None);
        search = request.GET.get('search', None)
        date_from_param =request.GET.get('date_from', None)
        date_to_param =request.GET.get('date_to', None)
        month_param =request.GET.get('month', None)
        product_id =request.GET.get('product_id', None)
        vendorId = request.GET.get("vendor_id", None)
        customerId = request.GET.get("customer_id", None)
        is_cancelled = request.GET.get("is_cancelled", "0") == "1"
        
        business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True, is_deleted = False).first()
        queryset = Invoice.objects.filter(business_profile=business_profile, is_deleted = is_cancelled).order_by("-id")
        paginator = self.pagination_class()
        
        if vendorId:
            queryset = queryset.filter(vendor=vendorId)
        if customerId:
            queryset = queryset.filter(customer=customerId)
        if product_id:
            invoiceIds = list(InvoiceItem.objects.filter(product_id=product_id).values_list('invoice_id', flat=True))
            queryset = queryset.filter(id__in=invoiceIds)
        if is_purchase_filter is not None:
           queryset = queryset.filter(is_purchase=int(is_purchase_filter))
        if search:
                queryset = queryset.filter( 
                      Q(customer__customer_name__icontains=search)|
                      Q(invoice_counter__icontains=search) |
                      Q(payment_type__icontains=search)
                  )
        if date_from_param and date_to_param:
           date_from = datetime.datetime.strptime(date_from_param, '%Y-%m-%d').date()
           date_to = datetime.datetime.strptime(date_to_param, '%Y-%m-%d').date()
           queryset = queryset.filter(order_date_time__date__range=(date_from, date_to))
        if month_param:
           month = int(month_param)
           queryset = queryset.filter(order_date_time__month=month)
        
            
        result_page = paginator.paginate_queryset(queryset, request, view=self)
        current_domain = request.build_absolute_uri('/media').rstrip('/')
        serializer = InvoiceCreateSerializer(result_page, context={"request": request, 'current_domain': current_domain}, many=True)
        total_length_before_pagination = queryset.count();
        total_pages = paginator.page.paginator.num_pages
        response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"Invoice Found Successfully!",
                        "data": serializer.data,
                        "total_length_before_pagination":total_length_before_pagination,
                        "total_pages":total_pages,
                        "next": paginator.get_next_link(),  # Include the next page link
            }       
        return Response(response)   

    
class InvoiceRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, id):
        try:
            return Invoice.objects.get(id=id)
        except Invoice.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def get(self, request, id):
        try:
            business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True, is_deleted = False).first()
            # Get the invoice instance
            invoice_instance = Invoice.objects.filter(
                business_profile=business_profile,
                id=id).first()
            if not invoice_instance:
                return Response({
                    "status_code": 404,
                    "status": "failed",
                    "message": "Invoice Not Found"
                }, status=404)
            
            # Get the current domain for media files
            current_domain = request.build_absolute_uri('/media').rstrip('/')
            
            # Get the invoice items related to the invoice
            invoice_items = InvoiceItem.objects.filter(invoice_id=id, is_deleted=False)
            
            # Get the product IDs from the invoice items
            # product_ids = invoice_items.values_list('product_id', flat=True)
            
            # Get the product data
            # product_data = queryset = Product.objects.filter(id__in=product_ids)\
            #     .prefetch_related(
            #         Prefetch('batches', queryset=Batches.objects.filter(is_deleted=False))
            #     )\
            #     .annotate(total_remaining_quantity=Sum('batches__remaining_quantity'))

            # Serialize the invoice
            # serializer = InvoiceCreateSerializer(invoice_instance, context={'current_domain': current_domain})
            
            # Serialize the product data with related batches and quantities
            # product_serializer = ProductdataSerializer(product_data, many=True, context={"invoice_items": invoice_items})

            response = {
                "status_code": 200,
                "status": "success",
                "message": "Invoice Found Successfully!",
                "data": InvoiceItemSerializer(invoice_items, many=True).data,
            }
            return Response(response)
        
        except Exception as e:
            print(e)
            return Response({
                "status_code": 500,
                "status": "failed",
                "message": "An error occurred while retrieving the invoice details."
            }, status=500)
            
    def put(self, request, id):
        try:
            instance = self.get_object(id)
            business_profile = BusinessProfile.objects.filter(user_profile_id=request.user.id,is_active=True, is_deleted = False)
            request.data["business_profile"] = business_profile.first().id
            pre_paid = instance.paid_amount or 0.00
            if instance.payment_type == "pay_letter" and request.data["payment_type"] == "pay_letter":
                request.data["status"] = 1
                request.data["remaining_total"] = request.data["grand_total"]

            elif instance.payment_type == "pay_letter" and request.data["payment_type"] == "remain_payment":
                request.data["status"] = 2
                paid = request.data.get("paid_amount")
                request.data["paid_amount"] = pre_paid + paid
                request.data["remaining_total"] = instance.remaining_total - paid

            elif instance.payment_type == "pay_letter" and request.data["payment_type"] == "paid":
                request.data["status"] = 3
                request.data["remaining_total"] = 0
                
            elif instance.payment_type == "remain_payment" and request.data["payment_type"] == "remain_payment":
                request.data["status"] = 2
                paid = request.data.get("paid_amount")
                request.data["paid_amount"] = pre_paid + paid
                request.data["remaining_total"] = instance.remaining_total - paid

            elif instance.payment_type == "remain_payment" and request.data["payment_type"] == "paid":
                request.data["status"] = 3
                request.data["remaining_total"] = 0 
            elif instance.payment_type =="paid":
                response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"payment done allreday",}
                return Response(response)
                             
            serializer = InvoiceSerializer(instance, data=request.data)
            if serializer.is_valid():
                serializer.save()

                customer = get_object_or_404(Customer, id=request.data["customer"])
                data = update_pdf(id,customer,business_profile,pre_paid)
                invoices = invoice_pdf_create(request,data,id)
                current_domain = request.build_absolute_uri('/media').rstrip('/')
                invoiceserializer = InvoiceCreateSerializer(invoices,context={'current_domain': current_domain})

                response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"Invoice updated Successfully!",
                        "data": invoiceserializer.data
                    }
                return Response(response)
            
            else:
                response = {
                        "status_code": 404,
                        "status": "error",
                        "message":"Invoice not updated ",
                        "data": serializer.errors
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

    def delete(self, request, id):
        instance = self.get_object(id)
        instance.delete()
        response = {
                "status_code": 204,
                "status": "success",
                "message": "Invoice Deleted"
            }
        return Response(response)

# class InvoiceOrderAPI(APIView):
#     permission_classes = [IsAuthenticated]
#     def post(self, request):
#         try:
#             with transaction.atomic():
#                 # Extract data from request
#                 product_quantity = request.data.pop("product_and_quantity")
#                 customer_id = request.data.get("customer")
#                 payment_type = request.data.get("payment_type")
#                 payment_option = request.data.get("payment_option")
#                 paid_amount = request.data.get("paid_amount", 0.00)
#                 tax = request.data.get("tax", 0.00)
#                 discount = request.data.get("discount", 0.00)
#                 grand_total = request.data.get("grand_total", 0.00)
#                 remaining_total = request.data.get("remaining_total", grand_total)
#                 sub_total = request.data.get("sub_total", 0.00)

#                 # Validate payment type
#                 valid_payment_types = ["pay_letter", "remain_payment", "paid"]
#                 if payment_type not in valid_payment_types:
#                     return Response({"status_code": 200, "status": "error", "message": "Please select a valid payment type"})

#                 product_ids = []
#                 for item in product_quantity:
#                     prod = Product.objects.select_for_update().filter(id=item["productId"]).first()
#                     if not prod:
#                         return Response({"status_code": 200, "status": "error", "message": f"Product with id {item['productId']} not found"})
#                     if prod.remaining_quantity and prod.remaining_quantity <= 0:
#                         return Response({"status_code": 200, "status": "error", "message": "Product out of stock. Please update your inventory."})
#                     if item["quantity"] > prod.remaining_quantity:
#                         return Response({"status_code": 200, "status": "error", "message": "Insufficient stock. You don't have enough quantity for the requested product."})
#                     product_ids.append({"productId": prod.id, "quantity": item["quantity"]})

#                 # Get business profile and customer
#                 business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True, is_deleted = False).first()
#                 customer = get_object_or_404(Customer, id=customer_id)
#                 is_purchase = request.data.get("is_purchase", customer.is_purchase)
#                 # Create invoice
#                 invoice = Invoice.objects.create(
#                     business_profile=business_profile,
#                     customer=customer,
#                     is_purchase=is_purchase,
#                     payment_type=payment_type,
#                     payment_option=payment_option,
#                     grand_total=grand_total,
#                     sub_total=sub_total,
#                     paid_amount=paid_amount,
#                     discount=discount,
#                     tax=tax,
#                     status=200,
#                     remaining_total=remaining_total,
#                     order_date_time=timezone.now()
#                 )
                
#                 # Create invoice items and update product quantities
#                 invoice_item_data = []
#                 product_data = []
#                 for item in product_ids:
#                    product = Product.objects.select_for_update().get(id=item["productId"])
#                    price = float(product.sales_price) * item["quantity"]
#                    invoice_item_data.append(InvoiceItem(
#                      invoice=invoice,
#                      product=product,
#                      price=price,
#                      quantity=item["quantity"],
#                      is_deleted= False,
#                      invoice_id= invoice.id,
#                      product_id= product.id
#                    ))
                   
#                    product.remaining_quantity -= item["quantity"]
#                    product.save()
#                    set_remaining_product_quantity(product)
#                    product_data.append(ProductSerializer(product).data)
                   
#                 # Bulk create invoice items
#                 if invoice_item_data:
#                      InvoiceItem.objects.bulk_create(invoice_item_data)
                
#                 # Prepare response data
#                 current_domain = request.build_absolute_uri('/media').rstrip('/')
#                 invoice_item = InvoiceItemSerializer(invoice_item_data, many=True).data
#                 invoice_data = InvoiceCreateSerializer(invoice).data
#                 id = range(1, len(product_data) + 1)
#                 content = list(zip(product_data, invoice_item, id))
#                 data = {
#                     "invoice": invoice_data,
#                     "content": content,
#                     "order_date": timezone.now(),
#                     "business_profile": business_profile,
#                     "customer": customer,
#                     "flage": page_break(id),
#                 }

#                 # Generate invoice PDF
#                 invoice_id = invoice.id
#                 invoices = invoice_pdf_create(request, data, invoice_id)

#                 # Prepare response
#                 response = {
#                     "status_code": 200,
#                     "status": "success",
#                     "message": "Invoice order data",
#                     "invoice": InvoiceCreateSerializer(invoices, context={'current_domain': current_domain}).data,
#                 }
#                 return Response(response)

#         except Exception as e:
#             print(f"Error: {e}")
#             response = {
#                 "status_code": 500,
#                 "status": "error",
#                 "message": f"Internal server error: {e}"
#             }
#             return Response(response)

class PurchaseInvoiceAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            with transaction.atomic():
                data = request.data

                # Extract data from request
                product_quantity = data.pop("product_and_quantity", [])
                vendor_id = data.get("vendor")
                payment_type = data.get("payment_type")
                payment_option = data.get("payment_option")
                paid_amount = data.get("paid_amount", 0.00)
                tax = data.get("tax", 0.00)
                discount = data.get("discount", 0.00)
                grand_total = data.get("grand_total", 0.00)
                remaining_total = data.get("remaining_total", grand_total)
                sub_total = data.get("sub_total", 0.00)
                invoice_counter = data.get("invoice_counter")
                ewaybill_number = data.get("ewaybill_number")
                description = data.get("description")

                # Ensure vendor_id is provided
                if not vendor_id:
                    return Response({"status_code": 400, "status": "error", "message": "vendor_id must be provided"})

                # Validate payment type
                valid_payment_types = ["pay_later", "remain_payment", "paid"]
                if payment_type not in valid_payment_types:
                    return Response({"status_code": 400, "status": "error", "message": "Please select a valid payment type"})

                # Get business profile
                business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
                if not business_profile:
                    return Response({"status_code": 400, "status": "error", "message": "Active business profile not found"})

                vendor = get_object_or_404(Vendor, id=vendor_id, business_profile=business_profile ) if vendor_id else None

                # Create invoice
                invoice = Invoice.objects.create(
                    business_profile=business_profile,
                    vendor=vendor,
                    is_purchase=True,
                    payment_type=payment_type,
                    payment_option=payment_option,
                    grand_total=grand_total,
                    sub_total=sub_total,
                    paid_amount=paid_amount,
                    discount=discount,
                    tax=tax,
                    status=200,
                    remaining_total=remaining_total,
                    invoice_counter=invoice_counter,
                    order_date_time=timezone.now(),
                    ewaybill_number=ewaybill_number,
                    description=description
                )

                # Create invoice items and batches
                items = self.create_invoice_items(invoice, product_quantity)

                # Prepare response data
                current_domain = request.build_absolute_uri('/media').rstrip('/')
                invoice_data = InvoiceCreateSerializer(invoice).data
                id_range = range(1, len(product_quantity) + 1)
                
                data = {
                    "invoice": invoice_data,
                    "content": items,
                    "order_date": timezone.now(),
                    "business_profile": business_profile,
                    "customer": vendor,
                    "flag": page_break(id_range),
                }
                # Generate invoice PDF
                invoices = invoice_pdf_create(request, data, invoice.id)
                # Prepare response
                response = {
                    "status_code": 200,
                    "status": "success",
                    "message": "Invoice order data",
                    "invoice": InvoiceCreateSerializer(invoices, context={'current_domain': current_domain}).data,
                }
                return Response(response)

        except ValidationError as e:
            return Response({"status_code": 400, "status": "error", "message": str(e)})

        except Exception as e:
            print(f"Error: {e}")
            return Response({"status_code": 500, "status": "error", "message": f"Internal server error: {e}"})

    def create_invoice_items(self, invoice, product_batch):
        invoice_item_data = []
        for item in product_batch:
            batch_data = item["batch"]
            batch = Batches.objects.create(
                product_id=item["productId"],
                business_profile=invoice.business_profile,
                **batch_data
            )
            product = batch.product
            price = float(batch.sales_price) * batch_data["total_quantity"]
            invoice_item_data.append(InvoiceItem(
                invoice=invoice,
                product=product,
                price=price,
                deal_quantity=batch_data["deal_quantity"],
                quantity=batch_data["total_quantity"],
                is_deleted=False,
                batch=batch
            ))
        if invoice_item_data:
            items = InvoiceItem.objects.bulk_create(invoice_item_data)
            return items


    def put(self, request, invoice_id):
        try:
            with transaction.atomic():
                
                data = request.data
                
                # Get business profile
                business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
               
                if not business_profile:
                    return Response({"status_code": 400, "status": "error", "message": "Active business profile not found"}, status=status.HTTP_400_BAD_REQUEST)

                vendor_id = data.get("vendor")
                # Ensure vendor_id is provided
                if not vendor_id:
                    return Response({"status_code": 400, "status": "error", "message": "vendor_id must be provided"}, status=status.HTTP_400_BAD_REQUEST)
                
                vendor = get_object_or_404(Vendor, id=vendor_id)
                
                # Fetch the existing invoice
                invoice = get_object_or_404(Invoice, id=invoice_id, is_purchase=True, vendor=vendor, business_profile=business_profile)

                product_quantity = data.pop("product_and_quantity", [])
                payment_type = data.get("payment_type", invoice.payment_type)
                payment_option = data.get("payment_option", invoice.payment_option)
                paid_amount = data.get("paid_amount", invoice.paid_amount)
                tax = data.get("tax", invoice.tax)
                discount = data.get("discount", invoice.discount)
                grand_total = data.get("grand_total", invoice.grand_total)
                remaining_total = data.get("remaining_total", grand_total)
                sub_total = data.get("sub_total", invoice.sub_total)
                invoice_counter = data.get("invoice_counter", invoice.invoice_counter)
                ewaybill_number = data.get("ewaybill_number", invoice.ewaybill_number)
                description = data.get("description", invoice.description)

                # Validate payment type
                valid_payment_types = ["pay_later", "remain_payment", "paid"]
                if payment_type not in valid_payment_types:
                    return Response({"status_code": 400, "status": "error", "message": "Please select a valid payment type"}, status=status.HTTP_400_BAD_REQUEST)

                # Update invoice
                invoice.payment_type = payment_type
                invoice.payment_option = payment_option
                invoice.grand_total = grand_total
                invoice.sub_total = sub_total
                invoice.paid_amount = paid_amount
                invoice.discount = discount
                invoice.tax = tax
                invoice.remaining_total = remaining_total
                invoice.invoice_counter = invoice_counter
                invoice.ewaybill_number = ewaybill_number
                invoice.description = description
                invoice.save()
                # Update invoice items and batches
                self.update_invoice_items(invoice, product_quantity, business_profile)

                # Prepare response data
                current_domain = request.build_absolute_uri('/media').rstrip('/')
                invoice_data = InvoiceCreateSerializer(invoice).data
                id_range = range(1, len(product_quantity) + 1)

                data = {
                    "invoice": invoice_data,
                    "order_date": timezone.now(),
                    "business_profile": business_profile,
                    "customer": vendor,
                    "flag": page_break(id_range),
                }
                
                # Generate invoice PDF
                invoices = invoice_pdf_create(request, data, invoice.id)

                # Prepare response
                response = {
                    "status_code": 200,
                    "status": "success",
                    "message": "Invoice updated successfully",
                    "invoice": InvoiceCreateSerializer(invoices, context={'current_domain': current_domain}).data,
                }
                return Response(response, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"status_code": 400, "status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Error: {e}")
            return Response({"status_code": 500, "status": "error", "message": f"Internal server error: {e}"})

    def update_invoice_items(self, invoice, product_quantity, business_profile):
        # Delete existing invoice items for the invoice
        InvoiceItem.objects.filter(invoice=invoice).delete()

        invoice_item_data = []
        
        for item in product_quantity:
            batch_data = item.get("batch", {})
            batchId = batch_data.get('id', None)
            if not batchId:
                productId = item.get("productId")
                batch_data["product"] = Product.objects.filter(id=productId).first();
                batch_data["business_profile"] = business_profile
    
            # Update or create Batch object
            batch, created = Batches.objects.update_or_create(
                pk=batchId,
                defaults=batch_data
            )
            
            product = batch.product
            price = float(batch.sales_price) * batch.total_quantity
            print(product)
            invoice_item = InvoiceItem(
                invoice=invoice,
                product=product,
                price=price,
                deal_quantity=item.get("deal_quantity", batch.deal_quantity),
                quantity = batch.total_quantity,
                is_deleted=False,
                batch=batch
            )
            
            invoice_item_data.append(invoice_item)
        
        # Bulk create all new invoice items
        if invoice_item_data:
            InvoiceItem.objects.bulk_create(invoice_item_data)
            
    def delete(self, request, invoice_id):
        try:
            # Get business profile
            business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
            if not business_profile:
                return Response({"status_code": 400, "status": "error", "message": "Active business profile not found"})
            
            invoice = get_object_or_404(Invoice, id=invoice_id, is_deleted=False, business_profile=business_profile)
            if invoice:
                InvoiceItem.objects.filter(invoice=invoice).delete() # invoice items permanently
                invoice.delete()
                
            return Response({"status_code": 200, "status": "success", "message": "Invoice successfully deleted"})
        
        except Exception as e:
            return Response({"status_code": 500, "status": "error", "message": f"Internal server error: {e}"})  
                    

class InvoiceOrderAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            with transaction.atomic():
                data = request.data

                # Extract data from request
                product_quantity = data.pop("product_and_quantity", [])
                customer_id = data.get("customer")
                payment_type = data.get("payment_type")
                payment_option = data.get("payment_option")
                paid_amount = data.get("paid_amount", 0.00)
                tax = data.get("tax", 0.00)
                discount = data.get("discount", 0.00)
                grand_total = data.get("grand_total", 0.00)
                remaining_total = data.get("remaining_total", grand_total)
                sub_total = data.get("sub_total", 0.00)
                invoice_counter = data.get("invoice_counter")

                # Ensure at least one of customer_id or vendor_id is provided
                if not customer_id:
                    return Response({"status_code": 400, "status": "error", "message": "customer_id must be provided"})

                # Validate payment type
                valid_payment_types = ["pay_later", "remain_payment", "paid"]
                if payment_type not in valid_payment_types:
                    return Response({"status_code": 400, "status": "error", "message": "Please select a valid payment type"})

                # Validate and prepare product IDs
                product_ids = self.validate_and_prepare_product_ids(product_quantity)

                # Get business profile
                business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
                if not business_profile:
                    return Response({"status_code": 400, "status": "error", "message": "Active business profile not found"})

                # Get customer or vendor
                customer = get_object_or_404(Customer, id=customer_id) if customer_id else None
                
                # Create invoice
                invoice = Invoice.objects.create(
                    business_profile=business_profile,
                    customer=customer,
                    is_purchase=False,
                    payment_type=payment_type,
                    payment_option=payment_option,
                    grand_total=grand_total,
                    sub_total=sub_total,
                    paid_amount=paid_amount,
                    discount=discount,
                    tax=tax,
                    status=200,
                    remaining_total=remaining_total,
                    invoice_counter=invoice_counter,
                    order_date_time=timezone.now()
                )
                
                # Create invoice items and update batch quantities
                items = self.create_invoice_items(invoice, product_ids)
                
                # Prepare response data
                current_domain = request.build_absolute_uri('/media').rstrip('/')
                invoice_data = InvoiceCreateSerializer(invoice).data
                id_range = range(1, len(product_quantity) + 1)
                
                data = {
                    "invoice": invoice_data,
                    "content": items,
                    "order_date": timezone.now(),
                    "business_profile": business_profile,
                    "customer": customer,
                    "flage": page_break(id_range),
                }
                # Generate invoice PDF
                invoice_id = invoice.id
                invoices = invoice_pdf_create(request, data, invoice_id)
                # Prepare response
                response = {
                    "status_code": 200,
                    "status": "success",
                    "message": "Invoice order data",
                    "invoice": InvoiceCreateSerializer(invoices, context={'current_domain': current_domain}).data,
                }
                return Response(response)

        except ValidationError as e:
            return Response({"status_code": 400, "status": "error", "message": str(e)})

        except Exception as e:
            print(f"Error: {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": f"Internal server error: {e}"
            }
            return Response(response)

    def validate_and_prepare_product_ids(self, product_quantity):
        product_ids = []
        for item in product_quantity:
            batch = Batches.objects.select_for_update().filter(id=item["batchId"]).first()
            if not batch:
                raise ValidationError(f"Batch with id {item['batchId']} not found")
            if batch.remaining_quantity <= 0:
                raise ValidationError("Product out of stock. Please update your inventory.")
            if item["quantity"] > batch.remaining_quantity:
                raise ValidationError("Insufficient stock. You don't have enough quantity for the requested product.")
            product_ids.append({"batchId": batch.id, "quantity": item["quantity"]})
        return product_ids

    def create_invoice_items(self, invoice, product_ids):
        invoice_item_data = []
        for item in product_ids:
            batch = Batches.objects.select_for_update().get(id=item["batchId"])
            product = batch.product
            price = float(batch.sales_price) * item["quantity"]
            invoice_item_data.append(InvoiceItem(
                invoice=invoice,
                product=product,
                price=price,
                quantity=item["quantity"],
                is_deleted=False,
                invoice_id=invoice.id,
                product_id=product.id,
                batch=batch
            ))
            batch.remaining_quantity -= item["quantity"]
            batch.save()
            set_remaining_product_quantity(batch)
        if invoice_item_data:
            items = InvoiceItem.objects.bulk_create(invoice_item_data)
            return items
            
    def put(self, request):
        try:
            with transaction.atomic():
                # Retrieve existing invoice
                invoice = get_object_or_404(Invoice, id=request.data["invoice_id"])
                
                # Extract data from request
                product_quantity = request.data.pop("product_and_quantity", [])
                customer_id = request.data.get("customer")
                payment_type = request.data.get("payment_type")
                payment_option = request.data.get("payment_option")
                paid_amount = request.data.get("paid_amount", 0.00)
                tax = request.data.get("tax", 0.00)
                discount = request.data.get("discount", 0.00)
                grand_total = request.data.get("grand_total", 0.00)
                remaining_total = request.data.get("remaining_total", grand_total)
                sub_total = request.data.get("sub_total", 0.00)

                # Validate payment type
                valid_payment_types = ["pay_letter", "remain_payment", "paid"]
                if payment_type not in valid_payment_types:
                    return Response({"status_code": 400, "status": "error", "message": "Please select a valid payment type"})

                # Fetch batches and validate quantities
                product_ids = []
                batches_to_update = []
                for item in product_quantity:
                    batch = Batches.objects.select_for_update().filter(id=item["batchId"]).first()
                    if not batch:
                        return Response({"status_code": 404, "status": "error", "message": f"Batch with id {item['batchId']} not found"})
                    if item["quantity"] > batch.remaining_quantity:
                        return Response({"status_code": 400, "status": "error", "message": "Insufficient stock. You don't have enough quantity for the requested product."})
                    product_ids.append({"batchId": batch.id, "quantity": item["quantity"]})
                    batches_to_update.append(batch)

                # Get business profile and customer
                business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
                 # Get customer or vendor
                customer = get_object_or_404(Customer, id=customer_id) if customer_id else None
                

                # Update invoice fields
                invoice.business_profile = business_profile
                invoice.customer = customer
                invoice.is_purchase = False
                invoice.payment_type = payment_type
                invoice.payment_option = payment_option
                invoice.grand_total = grand_total
                invoice.sub_total = sub_total
                invoice.paid_amount = paid_amount
                invoice.discount = discount
                invoice.tax = tax
                invoice.remaining_total = remaining_total
                invoice.order_date_time = timezone.now()
                invoice.save()

                # Delete existing invoice items and restore batch quantities
                existing_invoice_items = InvoiceItem.objects.filter(invoice=invoice)
                for item in existing_invoice_items:
                    batch = item.batch
                    batch.remaining_quantity += item.quantity
                    batch.save()
                existing_invoice_items.delete()

                # Create new invoice items and update batch quantities
                items = self.create_invoice_items(invoice, product_ids)

                # Prepare response data
                current_domain = request.build_absolute_uri('/media').rstrip('/')
                invoice_data = InvoiceCreateSerializer(invoice).data
                id_range = range(1, len(product_quantity) + 1)
                
                data = {
                    "invoice": invoice_data,
                    "content": items,
                    "order_date": timezone.now(),
                    "business_profile": business_profile,
                    "customer": customer,
                    "flage": page_break(id_range),
                }
                # Generate invoice PDF
                invoice_id = invoice.id
                invoices = invoice_pdf_create(request, data, invoice_id)

                # Prepare response
                response = {
                    "status_code": 200,
                    "status": "success",
                    "message": "Invoice updated successfully",
                    "invoice": InvoiceCreateSerializer(invoices, context={'current_domain': current_domain}).data,
                }
                return Response(response)

        except ValidationError as e:
            return Response({"status_code": 400, "status": "error", "message": str(e)})

        except Exception as e:
            print(f"Error: {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": f"Internal server error: {e}"
            }
            return Response(response)
        
    def delete(self, request, invoice_id):
        try:
            # Get business profile
            business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
            if not business_profile:
                return Response({"status_code": 400, "status": "error", "message": "Active business profile not found"})
            
            invoice = get_object_or_404(Invoice, id=invoice_id, is_deleted=False, business_profile=business_profile)
            if invoice:
                delete_invoice_items(invoice)
                invoice.delete()
            return Response({"status_code": 200, "status": "success", "message": "Invoice successfully deleted"})
        
        except Exception as e:
            return Response({"status_code": 500, "status": "error", "message": f"Internal server error: {e}"})  
        
def delete_invoice_items(invoice):
    invoice_items = InvoiceItem.objects.filter(invoice=invoice)

    for item in invoice_items:
        batch = item.batch
        batch.remaining_quantity += item.quantity
        batch.save()    
        # here we can delete invoice item as well 
         
class InvoiceSearch(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def get(self, request):
        
        try:
            businessprofile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True, is_deleted = False).first()
            search_query = request.GET.get('search')
            current_domain = request.build_absolute_uri('/media').rstrip('/')
            if search_query !="":
                innvoice = Invoice.objects.filter(business_profile=businessprofile, is_deleted = False).filter(
                    Q(customer__customer_name__icontains=search_query) |
                    Q(customer__phone_number__icontains=search_query) |
                    Q(order_date_time__icontains=search_query)                   
                )
                if innvoice:
                    businessprofile_innvoices = innvoice.filter(business_profile=businessprofile)
                    innvoice_serializer = InvoiceCreateSerializer(businessprofile_innvoices,context={"request":request,'current_domain': current_domain},many= True)
                    response = {
                        "status_code": 200,
                        "status": "success",
                        "message": "Customers and found successfully!",
                        "invoice": innvoice_serializer.data,
                    }
                    return Response(response)
                else:
                    msg = f"No results for {search_query}.\n Try checking your spelling or use more general terms"
                    print(msg)
                    response = {
                        "status_code": 200,
                        "status": "success",
                        "message": msg,
                        "invoice":[],
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
        

class InvoiceSort(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def post(self, request):
        try:
            business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True, is_deleted = False).first()
            queryset = business_profile.invoice_set.all()
            if "amount" in request.data.keys():
                if request.data["amount"] == "low to high":
                    queryset = queryset.order_by("grand_total")
                elif request.data["amount"] == "high to low":
                    queryset = queryset.order_by("-grand_total")
            elif "dbct" in request.data.keys():
                if request.data["dbct"] == "low to high":
                    queryset = queryset.order_by("remaining_total")
                elif request.data["dbct"] == "high to low":
                    queryset = queryset.order_by("-remaining_total")

            if "Payment_option" in request.data.keys():
                payment_filter = request.data["Payment_option"]
                if payment_filter == "credit":
                    queryset = queryset.filter(payment_option="paid").order_by("grand_total")
                elif payment_filter == "debit":
                    queryset = queryset.filter(payment_option="pay_letter").order_by("grand_total")
                elif payment_filter == "upi":
                    queryset = queryset.filter(payment_option="remain_payment").order_by("grand_total")
                elif payment_filter == "cash": 
                    queryset = queryset.filter(payment_option="remain_payment").order_by("grand_total")
                    
            if "payment_type" in request.data.keys():
                payment_type = request.data["payment_type"]
                if payment_type in ["remain_payment","paid","pay_letter"]:
                    queryset = queryset.filter(payment_type=payment_type)
                    
            if "status" in request.data.keys():
                status = request.data["status"]
                if status=='red':
                    queryset = queryset.filter(status=1).order_by("grand_total")
                elif status=='yellow':
                    queryset = queryset.filter(status=2).order_by("grand_total")
                elif status=='green':
                    queryset = queryset.filter(status=3).order_by("grand_total")

            if "start_date" in request.data.keys() and "end_date" in request.data.keys():
                start_date = request.data["start_date"]
                end_date = request.data["end_date"]

                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

                    # Filter invoices between start and end date (inclusive)
                    queryset = queryset.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
                    
                except ValueError as e:
                    print(f"error's {e}")
                    response = {
                        "status_code": 500,
                        "status": "error",
                        "message": f"Internal server error {e}"
                    }
                    return Response(response)

            paginator = self.pagination_class()
            current_domain = request.build_absolute_uri('/media').rstrip('/')
            invoice_result_page = paginator.paginate_queryset(queryset, request, view=self)
            total_length_before_pagination = queryset.count()
            total_pages = paginator.page.paginator.num_pages
            invoiceserializer = InvoiceCreateSerializer(invoice_result_page,context={'current_domain': current_domain},many = True)

            response = {
                    "status_code": 200,
                    "status": "success",
                    "message": "Invoice data",
                    "invoice": invoiceserializer.data,    
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

class InvoiceListChartView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def get(self , request):
        current_date = timezone.now()
        business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True, is_deleted = False).first()
        today_queryset = Invoice.objects.filter(business_profile=business_profile, created_at__date=current_date.date(), is_deleted = False)
        today_invoice = len(today_queryset)
        calculation = get_percentage(today_queryset,today_invoice)
        percentage_paid = calculation["percentage_paid"]
        percentage_remaining = calculation["percentage_remaining"]
        percentage_pay_letter = calculation["percentage_pay_letter"]
        payment_remaining = percentage_remaining+percentage_pay_letter
        
        data = [{"payment_received": percentage_paid,"focused":percentage_paid >= payment_remaining},
                {"payment_remaining": payment_remaining,"focused":payment_remaining > percentage_paid}]
        
        month_queryset = Invoice.objects.filter(business_profile=business_profile, created_at__month=current_date.month, created_at__year=current_date.year)
        bar_chart,total = get_barchart(month_queryset)

        increments = []
        try:
            value = len(str(int(total)))
            value =int('1'+(value-2)*"0")
            increment = (total+value) / 5
            for i in range(6):
                increments.append(str(int(increment * i)))
        except:
            increments = ['0', '1', '2', '3', '4', '5']
            
        queryset = Invoice.objects.filter(business_profile=business_profile)
        total_invoice = len(queryset)
        calculation = get_percentage(queryset,total_invoice)
        percentage_paid = calculation["percentage_paid"]
        percentage_remaining = calculation["percentage_remaining"]
        percentage_pay_letter = calculation["percentage_pay_letter"]

        payment_remaining = percentage_remaining+percentage_pay_letter
        greatest_percentage = max(percentage_paid, percentage_remaining, percentage_pay_letter )

        if percentage_paid == payment_remaining == percentage_pay_letter:
            result = 2
        elif percentage_paid == greatest_percentage:
            result = 1
        elif percentage_remaining == greatest_percentage:
            result = 2
        elif percentage_pay_letter == greatest_percentage:
            result = 3
        if percentage_paid == 0:
            result = 3
        
        score = {"score_percentage": percentage_paid,
                "score_status": result}
        
        invoice_data = {"invoices": total_invoice,
                        "credit": calculation["credit"],
                        "debit":calculation["debit"]
                        }
                
        response = {
            "status_code": 200,
            "status": "success",
            "message":"Invoice Found Successfully!",
            "today_invoces":today_invoice,
            "pie_cart":  data,
            "increments": increments,
            "bar_chart":bar_chart,
            "score":score,
            "total_invoces": invoice_data,}
         
        return Response(response)
    
class InvoiceCustomerSalesAnalytics(APIView): 
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # Get the current date and time with microsecond precision
        current_datetime = timezone.now()

        # Calculate the start and end dates of the current month
        current_month_start = current_datetime.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_end = current_month_start.replace(month=current_month_start.month + 1) - datetime.timedelta(microseconds=1)

        # Calculate the start and end dates of the previous month
        previous_month_end = current_month_start - datetime.timedelta(microseconds=1)
        previous_month_start = current_month_start - datetime.timedelta(days=previous_month_end.day)
        
        # Get the customerId from the request query parameters
        customerId = request.GET.get("customerId")
        product_id=request.GET.get('product_id', 0);

        # Get the business profile associated with the current user
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted = False).first()
        
        # Filter invoices by business profile and customer ID
        invoice_data = Invoice.objects.filter(business_profile=business_profile, is_deleted = False)
        
        if product_id:
            invoiceIds = list(InvoiceItem.objects.filter(product_id=product_id).values_list('invoice_id', flat=True))
            invoice_data = invoice_data.filter(id__in=invoiceIds)
        if customerId:
            invoice_data= invoice_data.filter(customer=customerId);
        
        # Calculate total sales, total outstanding, total cash, and total credit
        totals = invoice_data.aggregate(
            total_sales=Sum('sub_total'),
            total_outstanding=Sum('remaining_total'),
            total_cash=Sum('paid_amount'),
            total_credit=Sum('remaining_total', filter=Q(payment_type='pay_later'))
        )

        total_sales = totals['total_sales'] or 0
        total_outstanding = totals['total_outstanding'] or 0
        total_cash = totals['total_cash'] or 0
        total_credit = totals['total_credit'] or 0

        # Get sales data for the current month
        current_month_data = invoice_data.filter(order_date_time__range=(current_month_start, current_month_end)).annotate(
            day=TruncDay('order_date_time')
        ).values('day').annotate(total=Sum('grand_total')).order_by('day')

        # Get sales data for the previous month
        previous_month_data = invoice_data.filter(order_date_time__range=(previous_month_start, previous_month_end)).annotate(
            day=TruncDay('order_date_time')
        ).values('day').annotate(total=Sum('grand_total')).order_by('day')

       # Extracting total values for the current month
        current_month_values = [entry['total'] for entry in current_month_data]
        
        # Extracting total values for the previous month into a dictionary for efficient lookup
        previous_month_totals = {entry['day'].strftime('%Y-%m-%d'): entry['total'] for entry in previous_month_data}

        # Initialize previous month values list
        previous_month_values = []

       # Generating labels for each day in the current month
        x_labels = []

        for entry in current_month_data:
          day_str = entry['day'].strftime('%Y-%m-%d')
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

        response = {
            "status_code": 200,
            "status": "success",
            "message": "Invoice data retrieved successfully!",
            'data': {
                'total_sales': total_sales,
                'total_outstanding': total_outstanding,
                'total_cash': total_cash,
                'total_credit': total_credit,
                'previous_month_data': previous_month_values,
                'current_month_data': current_month_values,
                'current_month': current_month_values,
                'previous_month': previous_month_values,
                'x_labels': x_labels
            }
        }

        return Response(response)
    
    
class InvoiceMonthlySalesAnalytics(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # Get the business profile associated with the current user
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted = False).first()
        
        current_year = timezone.now().year
        
        invoices = Invoice.objects.filter(business_profile=business_profile, is_deleted = False, order_date_time__year=current_year)
        
        # Get the customerId from the request query parameters
        customerId = request.GET.get("customerId")
        
        if customerId:
            invoices= invoices.filter(customer=customerId);
        
        # Annotate invoices by month and year
        monthly_data = (invoices
                    .annotate(month=TruncMonth('order_date_time'))
                    .values('month')
                    .annotate(total_sub_total=Sum('sub_total'))
                    .order_by('month'))

        # Prepare the data for the response
        month_data = [item['total_sub_total'] for item in monthly_data]
        x_labels = [item['month'].strftime('%b %Y') for item in monthly_data]
        
        response = {
            "status_code": 200,
            "status": "success",
            "message": "Invoice data retrieved successfully!",
            'data': {
                "month_data": month_data,
                "x_labels": x_labels
            }
        }

        return Response(response)
    
