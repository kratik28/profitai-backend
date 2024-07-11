from datetime import datetime
from inventory.models import Product
from django.template.loader import render_to_string
from request_invoices.models import RequestInvoice
from django.core.files.base import ContentFile
from weasyprint import HTML
from django.core.files.storage import default_storage
    

def request_invoice_pdf_create(self, request, products_data):
    context = {
        'invoice': request,
        'content': products_data,
        'order_date': request.date_time,
        'business_profile': request.business_profile,  
    }
              
    html_content = render_to_string('request.html', context, request=request)
    invoice_pdf = HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf(zoom=1.0)
    file_name = f'invoice_{request.invoice_counter}.pdf'
    request.Invoice_pdf.save(file_name, ContentFile(invoice_pdf), save=True)
    pdf_url = request.build_absolute_uri(request.Invoice_pdf.url)