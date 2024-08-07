from django.contrib import admin
from django.urls import path
from profit_and_loss import views as profit_and_loss_view

urlpatterns = [
    path('', profit_and_loss_view.ProfitLossListView.as_view(), name='profit_loss_list'),
    path('expense/', profit_and_loss_view.ExpenseStatementListView.as_view(), name='expense_statement_list'),
    path('tax/download-profit_and_loss/', profit_and_loss_view.ProfitAndLossTaxCSVExcelAPIView.as_view(), name='download-profit-loss'),
    path('tax/', profit_and_loss_view.ProfitAndLossTaxStatementListView.as_view(), name='tax_profit_loss_list'),
    path('download-profit_and_loss/', profit_and_loss_view.ProfitLossCSVExcelAPIView.as_view(), name='download-profit-loss'),
]
