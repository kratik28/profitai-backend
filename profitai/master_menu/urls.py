from django.contrib import admin
from django.urls import path
from master_menu import views 

urlpatterns = [
    path('api/businesstype/list_create',views.BusinessTypecreateView().as_view(), name="businesstype-create"),
    path('api/businesstype/all/<int:id>',views.BusinessTypeRetrieveUpdateDestroyAPIView.as_view(), name="businesstype-all"),
    path('api/brandcreate/create',views.BrandcreateView().as_view(), name="Brandcreate-create"),
    path('api/brand/all/<int:id>',views.BrandRetrieveUpdateDestroyAPIView().as_view(), name="brand-all"),
    path('api/industry/create',views.IndustrycreateView().as_view(), name="industry-create"),
    path('api/industry/all/<int:id>',views.IndustryRetrieveUpdateDestroyAPIView().as_view(), name="industry-all"),
    path('api/ProductType/create',views.ProductTypecreateView().as_view(), name="ProductType-create"),
    path('api/ProductType/all/<int:id>',views.ProductTypeRetrieveUpdateDestroyAPIView().as_view(), name="ProductType-all"),
    path('api/size/create',views.SizecreateView().as_view(), name="size-create"),
    path('api/size/all/<int:id>',views.SizeRetrieveUpdateDestroyAPIView().as_view(), name="size-all")


]