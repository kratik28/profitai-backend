from django.contrib import admin
from django.urls import path
from invoice import views as invoice_view

urlpatterns = [
    path("api/invoice/customer/list",invoice_view.InvoiceCustomerListView().as_view()),
    path('api/invoice/listcreate',invoice_view.InvoiceListCreateView().as_view(), name="invoice-create"),
    path('api/invoice/details/<int:id>',invoice_view.InvoiceRetrieveUpdateDestroyAPIView().as_view(), name="invoice-create"),
    path('api/order/create/',invoice_view.InvoiceOrderAPI().as_view(), name="invoice-order"),
    path("api/invoice/search",invoice_view.InvoiceSearch().as_view(),name = "invoice-search"),
    path("api/invoice/sort/",invoice_view.InvoiceSort().as_view(),name = "invoice-sort"),
    path('api/invoice/analytics',invoice_view.InvoiceListChartView.as_view(),name='analytics'),
    path('api/invoice/monthly-sales-analytics',invoice_view.InvoiceCustomerSalesAnalytics.as_view(),name='monthly-sales-analytics')
]
