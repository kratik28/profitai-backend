from django.contrib import admin
from django.urls import path
from request_invoices import views as request_invoices_view

urlpatterns = [
    path("api/invoice/", request_invoices_view.RequestInvoiceAPIView().as_view()),
    path("api/invoice/<int:pk>/", request_invoices_view.RequestInvoiceAPIView().as_view())
]
