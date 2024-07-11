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
from .serializers import RequestInvoiceSerializer
from user_profile.models import BusinessProfile
from request_invoices.utils import request_invoice_pdf_create

class RequestInvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            with transaction.atomic():
                data = request.data

                # Extract data from request
                vendor_name = data.get("vendor_name")
                products_data = data.get("products", [])

                # Validate and create RequestInvoice
                business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
                if not business_profile:
                    return Response({"status_code": 400, "status": "error", "message": "Active business profile not found"})

                request_invoice = RequestInvoice.objects.create(
                    business_profile=business_profile,
                    vendor_name=vendor_name,
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
                serializer = RequestInvoiceSerializer(request_invoice, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"status": "success", "status_code": 200, "message": "Request Invoice updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

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