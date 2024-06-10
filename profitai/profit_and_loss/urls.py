from django.contrib import admin
from django.urls import path
from profit_and_loss import views as profit_and_loss_view

urlpatterns = [
    path('', profit_and_loss_view.ProfitLossListView.as_view(), name='profit_loss_list'),
]
