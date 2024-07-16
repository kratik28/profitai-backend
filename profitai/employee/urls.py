from django.contrib import admin
from django.urls import path
from employee import views as employee_view

urlpatterns = [
    path('', employee_view.EmployeeListCreateView.as_view(), name='employee_list_create'),
    path('<int:pk>/', employee_view.EmployeeDetailView.as_view(), name='employee_detail'),
    path('attendance/', employee_view.AttendanceListCreateView.as_view(), name='attendance_create'),
    path('attendance/mark-all-attendance/', employee_view.MarkAllAttendanceView.as_view(), name='mark_all_attendance'),
    path('attendance/<int:employee_id>/<int:pk>/', employee_view.AttendanceRetrieveUpdateDestroyView.as_view(), name='attendance-detail'),
]
