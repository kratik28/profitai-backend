from django.contrib import admin
from django.urls import path
from expense import views as expense_view

urlpatterns = [
    path('', expense_view.ExpenseListCreateView().as_view(), name='employee_list_create'),
    path('<int:pk>/', expense_view.ExpenseRetrieveUpdateDestroyView().as_view(), name='employee_detail')
]
