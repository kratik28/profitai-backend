from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import Expense
from .serializers import ExpenseSerializer
from user_profile.models import BusinessProfile
from user_profile.pagination import InfiniteScrollPagination

class ExpenseListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination

    def get(self, request):
        business_profile = BusinessProfile.objects.filter(user_profile=request.user, is_active=True, is_deleted=False).first()
        if not business_profile:
            return Response({"status": "error", "message": "Business profile not found."}, status=status.HTTP_404_NOT_FOUND)

        expenses = Expense.objects.filter(business_profile=business_profile)
        category = request.query_params.get('category')
        
        if category:
            expenses = expenses.filter(category=category)

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(expenses, request, view=self)
        total_length_before_pagination = expenses.count()
        total_pages = paginator.page.paginator.num_pages
        serializer = ExpenseSerializer(result_page, many=True)

        if request.query_params.get("type") == "all":
            response = {
                "status_code": 200,
                "status": "success",
                "message": "Expense records found successfully!",
                "data": ExpenseSerializer(expenses, many=True).data,
            }
        else:
            response = {
                "status_code": 200,
                "status": "success",
                "message": "Expense records found successfully!",
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
        serializer = ExpenseSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExpenseRetrieveUpdateDestroyView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            business_profile = BusinessProfile.objects.filter(user_profile=user, is_active=True, is_deleted=False).first()
            return Expense.objects.get(pk=pk, business_profile=business_profile)
        except Expense.DoesNotExist:
            return None

    def get(self, request, pk):
        expense = self.get_object(pk, request.user)
        if not expense:
            return Response({"status": "error", "message": "Expense not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ExpenseSerializer(expense)
        return Response(serializer.data)

    def put(self, request, pk):
        expense = self.get_object(pk, request.user)
        if not expense:
            return Response({"status": "error", "message": "Expense not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ExpenseSerializer(expense, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        expense = self.get_object(pk, request.user)
        if not expense:
            return Response({"status": "error", "message": "Expense not found."}, status=status.HTTP_404_NOT_FOUND)
        expense.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
