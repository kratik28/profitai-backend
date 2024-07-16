from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Employee, Attendance
from .serializers import EmployeeSerializer, AttendanceSerializer, AttendanceWithEmployeeSerializer
from user_profile.models import BusinessProfile
from user_profile.pagination import InfiniteScrollPagination
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.db import transaction


class EmployeeListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination

    def get(self, request):
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
        if not business_profile:
            return Response({"status": "error", "message": "Business profile not found."}, status=status.HTTP_404_NOT_FOUND)

        employees = Employee.objects.filter(business_profile=business_profile)
        search = request.GET.get('search', None)
        
        if search:
                employees = employees.filter( Q(name__icontains=search) )
                
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(employees, request, view=self)
        total_length_before_pagination = employees.count()
        total_pages = paginator.page.paginator.num_pages
        serializer = EmployeeSerializer(result_page, many=True)

        if request.query_params.get("type") == "all":
            response = {
                "status_code": 200,
                "status": "success",
                "message": "Employees found successfully!",
                "data": EmployeeSerializer(employees, many=True).data,
            }
        else:
            response = {
                "status_code": 200,
                "status": "success",
                "message": "Employees found successfully!",
                "data": serializer.data,
                "total_pages": total_pages,
                "total_length_before_pagination": total_length_before_pagination,
                "next": paginator.get_next_link(),
            }
        return Response(response)

    def post(self, request):
       
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
        if not business_profile:
            return Response({"status": "error", "message": "Business profile not found."}, status=status.HTTP_404_NOT_FOUND)
    
        data = request.data
        data['business_profile'] = business_profile.id
        serializer = EmployeeSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            business_profile = BusinessProfile.objects.filter(user_profile=user, is_active=True, is_deleted=False).first()
            return Employee.objects.get(pk=pk, business_profile=business_profile)
        except Employee.DoesNotExist:
            return None

    def get(self, request, pk):
        employee = self.get_object(pk, request.user)
        if not employee:
            return Response({"status": "error", "message": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = EmployeeSerializer(employee)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        employee = self.get_object(pk, request.user)
        if not employee:
            return Response({"status": "error", "message": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        serializer = EmployeeSerializer(employee, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data})
        return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        employee = self.get_object(pk, request.user)
        if not employee:
            return Response({"status": "error", "message": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
        employee.delete()
        return Response({"status": "success", "message": "Employee deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
    

class AttendanceListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination

    def get(self, request):
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
        if not business_profile:
            return Response({"status": "error", "message": "Business profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        
        attendances = Attendance.objects.filter(business_profile=business_profile).order_by("-date")
        employee_id = request.query_params.get('employee_id')
        
        if employee_id:
            attendances = attendances.filter(employee_id=employee_id)
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            start_date = parse_date(start_date)
            attendances = attendances.filter(date__gte=start_date)
        
        if end_date:
            end_date = parse_date(end_date)
            attendances = attendances.filter(date__lte=end_date)

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(attendances, request, view=self)
        total_length_before_pagination = attendances.count()
        total_pages = paginator.page.paginator.num_pages
        serializer = AttendanceWithEmployeeSerializer(result_page, many=True)

        if request.query_params.get("type") == "all":
            response = {
                "status_code": 200,
                "status": "success",
                "message": "Attendance records found successfully!",
                "data": AttendanceSerializer(attendances, many=True).data,
            }
        else:
            response = {
                "status_code": 200,
                "status": "success",
                "message": "Attendance records found successfully!",
                "data": serializer.data,
                "total_pages": total_pages,
                "total_length_before_pagination": total_length_before_pagination,
                "next": paginator.get_next_link(),
            }
        return Response(response)

    def post(self, request):
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
        if not business_profile:
            return Response({"status": "error", "message": "Business profile not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        data['business_profile'] = business_profile.id
        
        serializer = AttendanceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "message": "Attendance created successfully.", "data": serializer.data} , status=status.HTTP_201_CREATED)
        return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class AttendanceRetrieveUpdateDestroyView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user, employee_id, pk):
        try:
            business_profile = BusinessProfile.objects.filter(user_profile=user, is_active=True, is_deleted=False).first()
            if not business_profile:
                return None
            return Attendance.objects.get(pk=pk, employee_id=employee_id, business_profile=business_profile)
        except Attendance.DoesNotExist:
            return None

    def get(self, request, employee_id, pk):
        attendance = self.get_object(request.user, employee_id, pk)
        if not attendance:
            return Response({"status": "error", "message": "Attendance not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AttendanceSerializer(attendance)
        return Response({"status": "success", "message": "Attendance fetched successfully.", "data": serializer.data})

    def put(self, request, employee_id, pk):
        attendance = self.get_object(request.user, employee_id, pk)
        if not attendance:
            return Response({"status": "error", "message": "Attendance not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AttendanceSerializer(attendance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "message": "Attendance updated successfully.", "data": serializer.data})
        return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, employee_id, pk):
        attendance = self.get_object(request.user, employee_id, pk)
        if not attendance:
            return Response({"status": "error", "message": "Attendance not found."}, status=status.HTTP_404_NOT_FOUND)
        attendance.delete()
        return Response({"status": "success", "message": "Attendance deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
    
    
class MarkAllAttendanceView(APIView):
    @transaction.atomic
    def post(self, request):
        try:
            business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
            if not business_profile:
                return Response({"status_code": 400, "status": "error", "message": "Business profile not found"}, status=status.HTTP_400_BAD_REQUEST)

            date_str = request.data.get('date')
            if not date_str:
                return Response({"status_code": 400, "status": "error", "message": "Date is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            date = parse_date(date_str)
            if not date:
                return Response({"status_code": 400, "status": "error", "message": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST)

            employees = Employee.objects.filter(business_profile=business_profile)
            attendance_errors = []

            for employee in employees:
                if not Attendance.objects.filter(business_profile=business_profile, employee=employee, date=date).exists():
                    attendance_data = {
                        "business_profile": business_profile.id,
                        "employee": employee.id,
                        "date": date,
                        "check_in_time": "09:00:00",  # Default check-in time
                        "status": "Present"  # Default status
                    }
                    attendance_serializer = AttendanceSerializer(data=attendance_data)
                    if attendance_serializer.is_valid():
                        attendance_serializer.save()
                    else:
                        attendance_errors.append({employee.id: attendance_serializer.errors})

            if attendance_errors:
                transaction.set_rollback(True)
                return Response({"status_code": 400, "status": "error", "message": "Attendance creation failed", "errors": attendance_errors}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"status_code": 200, "status": "success", "message": "Attendance marked successfully for all employees!"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error: {e}")
            return Response({"status_code": 500, "status": "error", "message": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
