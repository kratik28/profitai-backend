from datetime import datetime
from inventory.models import Product
from django.template.loader import render_to_string
from invoice.models import Invoice, InvoiceItem
from django.core.files.base import ContentFile
from weasyprint import HTML
from django.core.files.storage import default_storage
from django.db.models import Sum


def set_remaining_product_quantity(product):
    sub_quantity = product.total_quantity // 3
    remaining_quantity = product.remaining_quantity

    if remaining_quantity <= sub_quantity * 1:
        product.status = 1
    elif sub_quantity * 1 < remaining_quantity <= sub_quantity * 2:
        product.status = 2
    else:
        product.status = 3

    product.save()

def page_break(id):
    id = len(id)
    if id > 14 and id < 18:
        flage = 'busines_name'
    # elif id >= 118 and id< 20:
    #     flage = 'subtotal_bar'
    else:
        flage = id
    return flage

def invoice_pdf_create(request,cont,id):
    instance_to_update = Invoice.objects.filter(id = id).first()
    invoice_number = instance_to_update.invoice_counter
    file_name = f'invoice_{invoice_number}.pdf'
    html_content = render_to_string('invoice-2.html', cont, request=request)
    Invoice_pdf = HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf(zoom=1.0)
    with default_storage.open(file_name, 'wb') as pdf_file:
        pdf_file.write(Invoice_pdf)
    instance_to_update.Invoice_pdf.save(file_name, ContentFile(Invoice_pdf), save=True)
    pdf_url = request.build_absolute_uri(instance_to_update.Invoice_pdf.url)

    return instance_to_update

def get_percentage(queryset,total_invoice):
    paid = 0
    remaining_payment = 0
    pay_later = 0
    
    for invoice in queryset:
        if invoice.payment_type == 'paid':
            paid += 1 
        elif invoice.payment_type == 'remain_payment':
            remaining_payment += 1
        elif invoice.payment_type == 'pay_letter':
            pay_later += 1

    if total_invoice != 0:
        percentage_paid = round((paid / total_invoice) * 100)
        percentage_remaining = round((remaining_payment / total_invoice) * 100)
        percentage_pay_letter = round((pay_later / total_invoice) * 100)
        percentage_total = round((total_invoice / total_invoice) * 100)
    else:
        percentage_paid = 0
        percentage_remaining = 0
        percentage_pay_letter = 0
        percentage_total = 0

    response = {"credit": paid,
                "debit": remaining_payment + pay_later,
                "percentage_paid":percentage_paid,
                "percentage_remaining":percentage_remaining,
                "percentage_pay_letter":percentage_pay_letter,
                }
    return response

def get_barchart(queryset):
    queryset = queryset.filter(payment_type__in=['paid', 'remain_payment', 'pay_letter'])
    totals_by_payment_type = queryset.values('payment_type').annotate(total_grand_total=Sum('grand_total'))
    totals_dict = {payment_type['payment_type']: payment_type['total_grand_total'] for payment_type in totals_by_payment_type}
    total_grand_total_paid = totals_dict.get('paid', 0)
    total_grand_total_remain_payment = totals_dict.get('remain_payment', 0)
    total_grand_total_pay_letter = totals_dict.get('pay_letter', 0)
    total = total_grand_total_paid + total_grand_total_remain_payment + total_grand_total_pay_letter
    response = [{"paid":int(total_grand_total_paid)},
                {"remain_payment":int(total_grand_total_remain_payment)},
                {"pay_letter":int(total_grand_total_pay_letter)}]
    return response, total

def update_pdf(id,customer,busines,pre_paid):
    invoice_data = Invoice.objects.filter(id=id).values()
    invoice_item =  InvoiceItem.objects.filter(invoice_id=id).values()
    product_ids = invoice_item.values_list('product_id', flat=True)
    product_data = Product.objects.filter(id__in=product_ids).values()
    total_product = range(1,len(product_data)+1)
    content = list(zip(product_data,invoice_item,total_product))
    
    data ={  
        "invoice":invoice_data,
        "content": content,
        "order_date": datetime.now(),
        "business_profile":busines,
        "customer":customer,
        "flage": page_break(total_product),
        "history":pre_paid
    }

    return data
