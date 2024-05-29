from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Employee, Attendance
from .serializers import EmployeeSerializer, AttendanceSerializer
from user_profile.models import BusinessProfile
from user_profile.pagination import InfiniteScrollPagination

class EmployeeListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination

    def get(self, request):
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
        if not business_profile:
            return Response({"status": "error", "message": "Business profile not found."}, status=status.HTTP_404_NOT_FOUND)

        employees = Employee.objects.filter(business_profile=business_profile)
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
        data['business_profile'] = business_profile
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
        business_profile = 1#BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
        if not business_profile:
            return Response({"status": "error", "message": "Business profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        
        attendances = Attendance.objects.filter(business_profile=business_profile)
        employee_id = request.query_params.get('employee_id')
        
        if employee_id:
            attendances = attendances.filter(employee_id=employee_id)

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(attendances, request, view=self)
        total_length_before_pagination = attendances.count()
        total_pages = paginator.page.paginator.num_pages
        serializer = AttendanceSerializer(result_page, many=True)

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
        data['business_profile'] = business_profile
        
        serializer = AttendanceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        return Response(serializer.data)

    def put(self, request, employee_id, pk):
        attendance = self.get_object(request.user, employee_id, pk)
        if not attendance:
            return Response({"status": "error", "message": "Attendance not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AttendanceSerializer(attendance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, employee_id, pk):
        attendance = self.get_object(request.user, employee_id, pk)
        if not attendance:
            return Response({"status": "error", "message": "Attendance not found."}, status=status.HTTP_404_NOT_FOUND)
        attendance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
