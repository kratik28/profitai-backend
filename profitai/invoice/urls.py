from django.contrib import admin
from django.urls import path
from invoice import views as invoice_view

urlpatterns = [
    path("api/invoice/customer/list",invoice_view.InvoiceCustomerListView.as_view()),
    path("api/invoice/vendor/list",invoice_view.InvoiceVendorListView.as_view()),
    path('api/invoice/listcreate',invoice_view.InvoiceListCreateView.as_view(), name="invoice-create"),
    path('api/invoice/details/<int:id>',invoice_view.InvoiceRetrieveUpdateDestroyAPIView.as_view(), name="invoice-create"),
    path('api/order/create/',invoice_view.InvoiceOrderAPI.as_view(), name="invoice-order"),
    path('api/purchase/create/',invoice_view.PurchaseInvoiceAPI.as_view(), name="purchase-invoice"),
     path('api/purchase/create/<int:invoice_id>/', invoice_view.PurchaseInvoiceAPI.as_view(), name='purchase-invoice-update'),
    path('api/order/create/<int:invoice_id>/', invoice_view.InvoiceOrderAPI.as_view(), name='invoice-delete'),
    path("api/invoice/search",invoice_view.InvoiceSearch.as_view(),name = "invoice-search"),
    path("api/invoice/sort/",invoice_view.InvoiceSort.as_view(),name = "invoice-sort"),
    path('api/invoice/analytics',invoice_view.InvoiceListChartView.as_view(),name='analytics'),
    path('api/invoice/monthly-sales-analytics',invoice_view.InvoiceCustomerSalesAnalytics.as_view(),name='monthly-sales-analytics'),
    path('api/invoice/invoice_month_wise-sales-analytics',invoice_view.InvoiceMonthlySalesAnalytics.as_view(),name='month-sales-analytics')
]
