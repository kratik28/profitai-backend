from django.shortcuts import get_object_or_404
from invoice.utils import get_barchart, get_percentage, invoice_pdf_create, page_break, set_remaining_product_quantity, update_pdf
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from inventory.models import Product
from inventory.serializers import ProductSerializer
from invoice.serializers import InvoiceCreateSerializer, InvoiceSerializer,InvoiceItemSerializer, ProductdataSerializer
from invoice.models import Invoice,InvoiceItem
from rest_framework.permissions import IsAuthenticated
from user_profile.models import BusinessProfile, Customer
from datetime import datetime
from django.db.models import Q, Max
from user_profile.pagination import InfiniteScrollPagination
from django.db import transaction

class InvoiceCustomerListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def get(self , request):
        customerId = request.GET.get("customer_id")
        business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
        invoice_item_data = Invoice.objects.filter(business_profile=business_profile,customer=customerId)
        queryset = invoice_item_data.filter(customer_id = customerId).order_by('-id')
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

        business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
        queryset = Invoice.objects.filter(business_profile=business_profile)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request, view=self)
        current_domain = request.build_absolute_uri('/media').rstrip('/')
        total_length_before_pagination = queryset.count()
        total_pages = paginator.page.paginator.num_pages
        serializer = InvoiceCreateSerializer(result_page,context={"request":request,'current_domain': current_domain},many= True)
        if request.query_params.get("type")=="all":
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"Invoice Found Successfully!",
                    "data":  InvoiceCreateSerializer(queryset,context={"request":request,'current_domain': current_domain},many= True).data,}
        else:
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

    def get(self,request,id):
        try:  
            invoice_instance = Invoice.objects.filter(id = id).first()
            current_domain = request.build_absolute_uri('/media').rstrip('/')
            invoice_item =  InvoiceItem.objects.filter(invoice_id=id).values()
            product_ids = invoice_item.values_list('product_id', flat=True)
            product_data = Product.objects.filter(id__in=product_ids)
        
            serializer = InvoiceCreateSerializer(invoice_instance,context={'current_domain': current_domain})
            product_serilizer = ProductdataSerializer(product_data,many=True,context={"invoice":invoice_instance})
            response = {
                        "status_code": 200,
                        "status": "success",
                        "message":"Invoice Found Successfully!",
                        "data": serializer.data,
                        "product_data":product_serilizer.data,
                    }
            return Response(response)
        except Exception as e:
            print(e)
            return Response( {"status_code": 500,
                            "status": "faild",
                            "message":"Invoice Not Found",})
        
    def put(self, request, id):
        try:
            instance = self.get_object(id)
            business_profile = BusinessProfile.objects.filter(user_profile_id=request.user.id,is_active=True)
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

class InvoiceOrderAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            with transaction.atomic():
                # Extract data from request
                product_quantity = request.data.pop("product_and_quantity")
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
                    return Response({"status_code": 200, "status": "error", "message": "Please select a valid payment type"})

                product_ids = []
                for item in product_quantity:
                    prod = Product.objects.select_for_update().filter(id=item["productId"]).first()
                    if not prod:
                        return Response({"status_code": 200, "status": "error", "message": f"Product with id {item['productId']} not found"})
                    if prod.remaining_quantity <= 0:
                        return Response({"status_code": 200, "status": "error", "message": "Product out of stock. Please update your inventory."})
                    if item["quantity"] > prod.remaining_quantity:
                        return Response({"status_code": 200, "status": "error", "message": "Insufficient stock. You don't have enough quantity for the requested product."})
                    product_ids.append({"productId": prod.id, "quantity": item["quantity"]})
                print("business_profile", "???")
                # Get business profile and customer
                business_profile =  BusinessProfile.objects.filter(is_active=True).first()
                customer = get_object_or_404(Customer, id=customer_id)
                
                # Create invoice
                invoice = Invoice.objects.create(
                    business_profile=business_profile,
                    customer=customer,
                    payment_type=payment_type,
                    payment_option=payment_option,
                    grand_total=grand_total,
                    sub_total=sub_total,
                    paid_amount=paid_amount,
                    discount=discount,
                    tax=tax,
                    status=200,
                    remaining_total=remaining_total,
                    order_date_time=datetime.now()
                )
                
                # Create invoice items and update product quantities
                invoice_item_data = []
                product_data = []
                for item in product_ids:
                   product = Product.objects.select_for_update().get(id=item["productId"])
                   price = float(product.sales_price) * item["quantity"]
                   invoice_item_data.append(InvoiceItem(
                     invoice=invoice,
                     product=product,
                     price=price,
                     quantity=item["quantity"],
                     is_deleted= False,
                     invoice_id= invoice.id,
                     product_id= product.id
                   ))
                   
                   product.remaining_quantity -= item["quantity"]
                   product.save()
                   set_remaining_product_quantity(product)
                   product_data.append(ProductSerializer(product).data)
                   
                # Bulk create invoice items
                if invoice_item_data:
                     InvoiceItem.objects.bulk_create(invoice_item_data)
                
                # Prepare response data
                current_domain = request.build_absolute_uri('/media').rstrip('/')
                invoice_item = InvoiceItemSerializer(invoice_item_data, many=True).data
                invoice_data = InvoiceCreateSerializer(invoice).data
                id = range(1, len(product_data) + 1)
                content = list(zip(product_data, invoice_item, id))
                data = {
                    "invoice": invoice_data,
                    "content": content,
                    "order_date": datetime.now(),
                    "business_profile": business_profile,
                    "customer": customer,
                    "flage": page_break(id),
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

        except Exception as e:
            print(f"Error: {e}")
            response = {
                "status_code": 500,
                "status": "error",
                "message": f"Internal server error: {e}"
            }
            return Response(response)
        
        
class InvoiceSearch(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    def get(self, request):
        
        try:
            businessprofile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
            search_query = request.GET.get('search')
            current_domain = request.build_absolute_uri('/media').rstrip('/')
            if search_query !="":
                innvoice = Invoice.objects.filter(business_profile=businessprofile).filter(
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
            business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
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
        current_date = datetime.now()
        business_profile = BusinessProfile.objects.filter(user_profile = request.user, is_active = True).first()
        today_queryset = Invoice.objects.filter(business_profile=business_profile, created_at__date=current_date.date())
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