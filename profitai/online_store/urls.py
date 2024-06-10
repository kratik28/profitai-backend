
    
from django.contrib import admin
from django.urls import path
from online_store import views as online_store_view

urlpatterns = [
    path('inventory-link-generate/', online_store_view.BusinessInventoryLinkAPIView.as_view(), name='inventory-link-list-create'),
    path('inventory-link-generate/<int:pk>/', online_store_view.BusinessInventoryLinkAPIView.as_view(), name='inventory-link-detail')
]
