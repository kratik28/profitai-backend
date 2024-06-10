# views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import BusinessInventoryLink
from inventory.models import Product
from user_profile.models import BusinessProfile
from .serializers import BusinessInventoryLinkSerializer
from user_profile.pagination import InfiniteScrollPagination



class BusinessInventoryLinkAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = InfiniteScrollPagination

    def get(self, request):
        business_profile = get_object_or_404(BusinessProfile, user_profile=request.user, is_active=True, is_deleted=False)
        links = BusinessInventoryLink.objects.filter(business_profile=business_profile)
        
        paginator = self.pagination_class()
        paginated_links = paginator.paginate_queryset(links, request, view=self)
        serializer = BusinessInventoryLinkSerializer(paginated_links, many=True)

        response = {
            "status_code": 200,
            "status": "success",
            "message": "Business Inventory Links found",
            "data": serializer.data,
            "total_length_before_pagination": len(links),
            "total_pages": paginator.page.paginator.num_pages,
            "next": paginator.get_next_link(),
        }
        return Response(response)

    def post(self, request):
        business_profile = get_object_or_404(BusinessProfile, user_profile=request.user, is_active=True, is_deleted=False)
        data = request.data
        data['business_profile'] = business_profile.id
        serializer = BusinessInventoryLinkSerializer(data=data)
        if serializer.is_valid():
            serializer.save(business_profile=business_profile)
            return Response({
                "status_code": 201,
                "status": "success",
                "message": "Business Inventory Link created successfully",
                "data": serializer.data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status_code": 400,
            "status": "error",
            "message": "Business Inventory Link creation failed",
            "errors": serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        link = get_object_or_404(BusinessInventoryLink, pk=pk)
        serializer = BusinessInventoryLinkSerializer(link, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status_code": 200,
                "status": "success",
                "message": "Business Inventory Link updated successfully",
                "data": serializer.data,
            }, status=status.HTTP_200_OK)
        return Response({
            "status_code": 400,
            "status": "error",
            "message": "Business Inventory Link update failed",
            "errors": serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        link = get_object_or_404(BusinessInventoryLink, pk=pk)
        link.delete()
        return Response({
            "status_code": 204,
            "status": "success",
            "message": "Business Inventory Link deleted successfully",
        }, status=status.HTTP_204_NO_CONTENT)
