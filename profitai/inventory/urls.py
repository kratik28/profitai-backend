from django.contrib import admin
from django.urls import path
from inventory import views as inventory_view

urlpatterns = [
    path('api/product/all/<int:id>',inventory_view.ProductRetrieveUpdateDestroyAPIView().as_view(), name="inventory-list"),
    path('api/product/listcreate',inventory_view.ProductListCreateView().as_view(), name="inventory-create"),
    path('api/product/batchescreate',inventory_view.BatchCreateView().as_view(), name="batches-create"),
    path("api/product/sort_filter",inventory_view.InventorySortingFilterAPI.as_view()),
    path("api/product/search",inventory_view.InventorySearchAPI.as_view()),
    path("api/product/quantity/check",inventory_view.InventoryProductQuantityCheckAPI.as_view()),
    path("api/product/analitycs",inventory_view.ProductAnalyticsAPI.as_view())
]