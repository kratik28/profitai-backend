from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField, Q, Avg
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncQuarter, TruncYear
from invoice.models import InvoiceItem, Invoice
from user_profile.models import BusinessProfile
from expense.models import Expense
from expense.serializers import ExpenseSerializer
from user_profile.pagination import InfiniteScrollPagination
from datetime import datetime


class ProfitLossListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    
    def get(self, request):
        customer_id = request.GET.get("customer_id")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        group_by = request.GET.get("group_by", "day")
        search = request.GET.get("search")
        
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
        
        # Filter invoice items based on the date range and business profile
        invoice_items = InvoiceItem.objects.filter(
            invoice__business_profile=business_profile,
            is_deleted=False,
            invoice__customer__isnull=False
        )
        
        if start_date and end_date:
            invoice_items = invoice_items.filter(invoice__order_date_time__range=[start_date, end_date])
        if customer_id:
            invoice_items = invoice_items.filter(invoice__customer_id=customer_id)
        if search:
            invoice_items = invoice_items.filter(
                Q(invoice__customer__customer_name__icontains=search) |
                Q(product__product_name__icontains=search) |
                Q(product__brand__icontains=search)
            )
        
        # Determine the truncation function based on group_by parameter
        if group_by == 'day':
            trunc_func = TruncDay
            group_by_field = 'invoice__order_date_time'
        elif group_by == 'week':
            trunc_func = TruncWeek
            group_by_field = 'invoice__order_date_time'
        elif group_by == 'month':
            trunc_func = TruncMonth
            group_by_field = 'invoice__order_date_time'
        elif group_by == 'quarter':
             trunc_func = TruncQuarter
             group_by_field = 'invoice__order_date_time'
        elif group_by == 'year':
            trunc_func = TruncYear
            group_by_field = 'invoice__order_date_time'
        elif group_by == 'customer':
            group_by_field = 'invoice__customer__customer_name'
        elif group_by == 'customer_zipcode':
            group_by_field = 'invoice__customer__zipcode'
        elif group_by == 'product_brand':
            group_by_field = 'product__brand'
        else:
            return Response({"status": "error", "message": "Invalid group_by parameter"}, status=400)

        # Calculate overall statistics
        overall_stats = invoice_items.aggregate(
            overall_volume_of_invoice=Count('invoice', distinct=True),
            overall_volume_of_goods=Sum('quantity'),
            overall_gross_sales=Sum(F('quantity') * F('price')),
            overall_gross_profit=Sum(F('quantity') * F('price')) - Sum(F('quantity') * F('batch__purchase_price')),
            overall_tax=Sum('invoice__tax'),
            overall_discount=Sum('invoice__discount'),
        )
        
        overall_stats = {key: value or 0 for key, value in overall_stats.items()}

        overall_stats['overall_gross_profit_percentage'] = (overall_stats['overall_gross_profit'] / overall_stats['overall_gross_sales']) * 100 if overall_stats['overall_gross_sales'] else 0
        overall_stats['overall_net_profit'] = overall_stats['overall_gross_profit'] - overall_stats['overall_tax'] - overall_stats['overall_discount']
        overall_stats['overall_net_profit_percentage'] = (overall_stats['overall_net_profit'] / overall_stats['overall_gross_sales']) * 100 if overall_stats['overall_gross_sales'] else 0

        # Annotate and aggregate data
        if group_by in ['customer', 'customer_zipcode', 'product_brand']:
            data = invoice_items.values(group_by_field).annotate(
                **{group_by: F(group_by_field)},
                volume_of_invoice=Count('invoice', distinct=True),
                volume_of_goods=Sum('quantity'),
                gross_sales=Sum(F('quantity') * F('price')),
                gross_profit=Sum(F('quantity') * F('price')) - Sum(F('quantity') * F('batch__purchase_price')),
                tax=Sum('invoice__tax'),
                discount=Sum('invoice__discount'),
                avg_buying_value=Avg('batch__purchase_price'),
                avg_selling_value=Avg('price')
            ).annotate(
                gross_profit_percentage=ExpressionWrapper(
                    (F('gross_profit') / F('gross_sales')) * 100,
                    output_field=DecimalField()
                ),
                net_profit=F('gross_profit') - F('tax') - F('discount'),
                net_profit_percentage=ExpressionWrapper(
                    (F('net_profit') / F('gross_sales')) * 100,
                    output_field=DecimalField()
                )
            ).order_by(group_by_field).values(
                group_by, 
                'volume_of_goods',
                'gross_sales',
                'gross_profit',
                'gross_profit_percentage',
                'tax',
                'discount',
                'net_profit',
                'net_profit_percentage',
                'avg_buying_value',
                'avg_selling_value'
            )
        else:
            data = invoice_items.annotate(
                date=trunc_func(group_by_field)
            ).values('date').annotate(
                volume_of_invoice=Count('invoice', distinct=True),
                volume_of_goods=Sum('quantity'),
                gross_sales=Sum(F('quantity') * F('price')),
                gross_profit=Sum(F('quantity') * F('price')) - Sum(F('quantity') * F('batch__purchase_price')),
                tax=Sum('invoice__tax'),
                discount=Sum('invoice__discount'),
            ).annotate(
                gross_profit_percentage=ExpressionWrapper(
                    (F('gross_profit') / F('gross_sales')) * 100,
                    output_field=DecimalField()
                ),
                net_profit=F('gross_profit') - F('tax') - F('discount'),
                net_profit_percentage=ExpressionWrapper(
                    (F('net_profit') / F('gross_sales')) * 100,
                    output_field=DecimalField()
                )
            ).order_by('date').values(
                'date',
                'volume_of_invoice',
                'volume_of_goods',
                'gross_sales',
                'gross_profit',
                'gross_profit_percentage',
                'tax',
                'discount',
                'net_profit',
                'net_profit_percentage'
            )
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(data, request, view=self)
        total_length_before_pagination = data.count()
        total_pages = paginator.page.paginator.num_pages

        return Response({
            "status_code": 200,
            "status": "success",
            "message": "Profit and Loss Statements Retrieved Successfully",
            "overall_stats": overall_stats,
            "data": result_page,
            "total_pages":total_pages,
            "total_length_before_pagination":total_length_before_pagination,
            "next": paginator.get_next_link(),
        })


class ExpenseStatementListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination
    
    def get(self, request, format=None):
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
        if not business_profile:
            return Response({"status": "error", "message": "Business profile not found."}, status=status.HTTP_404_NOT_FOUND)

        group_by = request.query_params.get('group_by', 'day')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        expenses = Expense.objects.filter(business_profile=business_profile)
        
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                expenses = expenses.filter(date__range=[start_date, end_date])
            except ValueError:
                return Response({"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        group_annotations = {
            'day': TruncDay('date'),
            'week': TruncWeek('date'),
            'month': TruncMonth('date'),
            'quarter': TruncQuarter('date'),
            'year': TruncYear('date')
        }

        if group_by in group_annotations:
            expenses = expenses.annotate(group=group_annotations[group_by]).values('group').annotate(total_cost=Sum('cost')).order_by('group')
        elif group_by == 'category':
            expenses = expenses.values('category').annotate(total_cost=Sum('cost')).order_by('category')
        else:
            return Response({"status": "error", "message": "Invalid group_by parameter"}, status=status.HTTP_400_BAD_REQUEST)

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(expenses, request, view=self)
        total_length_before_pagination = expenses.count()
        total_pages = paginator.page.paginator.num_pages
        
        return Response({
            "status_code": status.HTTP_200_OK,
            "status": "success",
            "message": "Expense Statements Retrieved Successfully",
            "data": result_page,
            "total_pages": total_pages,
            "total_length_before_pagination": total_length_before_pagination,
            "next": paginator.get_next_link(),
        })