from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .models import RequestInvoice, RequestInvoiceProduct
from .serializers import RequestInvoiceSerializer, RequestInvoiceProductSerializer
from user_profile.models import BusinessProfile, Vendor, Customer
from inventory.models import Product
from request_invoices.utils import request_invoice_pdf_create
from django.db.models import Q
from datetime import datetime
import os
from django.conf import settings
import random

class RequestInvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            with transaction.atomic():
                data = request.data

                # Extract data from request
                vendor_id = data.get("vendor")
                products_data = data.get("products", [])
                
                # Validate and create RequestInvoice
                business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
                if not business_profile:
                    return Response({"status_code": 400, "status": "error", "message": "Active business profile not found"})

                vendor = get_object_or_404(Vendor, id=vendor_id) if vendor_id else None
            
                request_invoice = RequestInvoice.objects.create(
                    business_profile=business_profile,
                    vendor=vendor,
                    date_time=timezone.now()
                )

                # Create RequestInvoiceProduct instances
                for product_data in products_data:
                    RequestInvoiceProduct.objects.create(
                        request_invoice=request_invoice,
                        product_name=product_data.get("product_name"),
                        brand=product_data.get("brand"),
                        qty=product_data.get("qty")
                    )
             
                # Generate PDF and update RequestInvoice
                context = {
                     'invoice': request_invoice,
                     'content': products_data,
                     'order_date': request_invoice.date_time,
                     'vendor': vendor,
                     'business_profile': request_invoice.business_profile,
                 }
              
                html_content = render_to_string('request_invoice.html', context, request=request)
                invoice_pdf = HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf(zoom=1.0)
                file_name = f'invoice_{request_invoice.invoice_counter}.pdf'
                request_invoice.Invoice_pdf.save(file_name, ContentFile(invoice_pdf), save=True)
                pdf_url = request.build_absolute_uri(request_invoice.Invoice_pdf.url)
               
               
                # Prepare response with detailed invoice data
                serializer = RequestInvoiceSerializer(request_invoice)
                response_data = {
                    "status": "success",
                    "status_code": 200,
                    "message": "Request Invoice created successfully",
                    "data": serializer.data,
                    "pdf_url": request.build_absolute_uri(request_invoice.Invoice_pdf.url)
                }
                return Response(response_data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Error: {e}")
            return Response({"status": "error", "message": f"Internal server error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
        if not business_profile:
            return Response({"status_code": 400, "status": "error", "message": "Active business profile not found"})

        request_invoices = RequestInvoice.objects.filter(business_profile=business_profile, is_deleted=False)
        
        # Get filter parameters
        search = request.GET.get('search')
        month = request.GET.get('month')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        vendor = request.GET.get('vendor_id')
    
        if vendor:
            request_invoices = request_invoices.filter(vendor=vendor) 
            
        if start_date and end_date:
            request_invoices = request_invoices.filter(date_time__range=[start_date, end_date])
            
        if month:
                try:
                     month_date = datetime.strptime(month, '%Y-%m')
                     request_invoices = request_invoices.filter(date_time__year=month_date.year, date_time__month=month_date.month)
                except ValueError:
                     return Response({"status_code": 400, "status": "error", "message": "Invalid month format. Use YYYY-MM."}, status=status.HTTP_400_BAD_REQUEST)
            
        if search:
            request_invoices = request_invoices.filter(
                Q(vendor__vendor_name__icontains=search) |
                Q(invoice_counter__icontains=search) 
            )
        
        
        serializer = RequestInvoiceSerializer(request_invoices, many=True)
        return Response({"status": "success", "status_code": 200, "data": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        try:
            with transaction.atomic():
                # Retrieve existing RequestInvoice
                business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
                if not business_profile:
                    return Response({"status_code": 400, "status": "error", "message": "Active business profile not found"})

                request_invoice = get_object_or_404(RequestInvoice, pk=pk, business_profile=business_profile, is_deleted=False)
                
                # Update RequestInvoiceProducts
                products_data = request.data.get('products', [])
                for product_data in products_data:
                    product_id = product_data.get('id')
                    if product_id:
                        product_data['request_invoice'] = request_invoice.id
                        product = get_object_or_404(RequestInvoiceProduct, id=product_id, request_invoice=request_invoice)
                        product_serializer = RequestInvoiceProductSerializer(product, data=product_data)
                        if product_serializer.is_valid():
                            product_serializer.save()
                        else:
                            return Response({"status": "error", "message": product_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        # If product_id is not provided, create a new product
                        product_data['request_invoice'] = request_invoice.id
                        new_product_serializer = RequestInvoiceProductSerializer(data=product_data)
                        if new_product_serializer.is_valid():
                            new_product_serializer.save()
                        else:
                            return Response({"status": "error", "message": new_product_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                
                # Generate PDF and update RequestInvoice
                vendor = request_invoice.vendor  # Assuming vendor is related to request_invoice
                context = {
                    'invoice': request_invoice,
                    'content': products_data,
                    'order_date': request_invoice.date_time,
                    'vendor': vendor,
                    'business_profile': request_invoice.business_profile,
                }
                
                html_content = render_to_string('request_invoice.html', context, request=request)
                invoice_pdf = HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf(zoom=1.0)
                file_name = f'invoice_{request_invoice.invoice_counter}.pdf'
                request_invoice.Invoice_pdf.save(file_name, ContentFile(invoice_pdf), save=True)
                pdf_url = request.build_absolute_uri(request_invoice.Invoice_pdf.url)
                serializer = RequestInvoiceSerializer(request_invoice)
                return Response({"status": "success", "status_code": 200, "message": "Request Invoice products updated and PDF regenerated successfully",  "data": serializer.data, "pdf_url": pdf_url}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error: {e}")
            return Response({"status": "error", "message": f"Internal server error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    def delete(self, request, pk):
        try:
            # Get and delete RequestInvoice
            business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
            if not business_profile:
                return Response({"status_code": 400, "status": "error", "message": "Active business profile not found"})

            request_invoice = get_object_or_404(RequestInvoice, pk=pk, business_profile=business_profile, is_deleted=False)
            request_invoice.delete()
            return Response({"status": "success", "status_code": 200, "message": "Request Invoice deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            print(f"Error: {e}")
            return Response({"status": "error", "message": f"Internal server error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
class GenerateInvoicePDF(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        
        # Extract data from request
        customer_id = data.get("customer")
        sub_total = data.get("sub_total")
        discount = data.get("discount")
        grand_total = data.get("grand_total")
        tax = data.get("tax")
        product_and_quantity = data.get("product_and_quantity", [])

        # Validate and create context
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
        if not business_profile:
            return Response({"status_code": 400, "status": "error", "message": "Active business profile not found"})
        
        customer = get_object_or_404(Customer, id=customer_id) if customer_id else None

        # Fetch full product details
        products_details = []
        for item in product_and_quantity:
            product_id = item.get("productId")
            quantity = item.get("quantity")
            batch_id = item.get("batchId")
            
            product = get_object_or_404(Product, id=product_id)
            product_detail = {
                'product': product,
                'quantity': quantity,
                'batch_id': batch_id
            }
            products_details.append(product_detail)

        random_number = random.randint(1000, 9999)
        context = {
            'customer': customer,
            'business_profile': business_profile,
            'sub_total': sub_total,
            'discount': discount,
            'grand_total': grand_total,
            'tax': tax,
            'id': random_number,
            'product_and_quantity': products_details,
            'order_date': datetime.now()
        }
        
        # Render HTML content
        html_content = render_to_string('estimate_invoice.html', context, request=request)
        
        # Generate PDF
        invoice_pdf = HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf(zoom=1.0)

        # Save PDF to a file
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_name = f'invoice_{timestamp}_{random_number}.pdf'
        file_path = os.path.join(reports_dir, file_name)
        
        with open(file_path, 'wb') as f:
            f.write(invoice_pdf)
        
        file_url = request.build_absolute_uri(f'/media/reports/{file_name}')
        
        
        return Response({"status": "success", "status_code": 200, "message": "Estimate Invoice generate successfully", "file_url": file_url}, status=status.HTTP_200_OK)
