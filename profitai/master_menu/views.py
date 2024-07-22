from django.shortcuts import render
from inventory.models import Product
from master_menu import models as master_mod  
from master_menu.serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

# Create your views here.

class BusinessTypecreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self , request):
        try:
            queryset =master_mod.BusinessType.objects.all()
            
            serializer = BusinessTypeSerializer(queryset,many= True)
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"BusinessType Found Successfully!",
                    "data": serializer.data
                }
            return Response(response)
        except Exception as e:
                response = {
                            "status_code": 200,
                            "status": "success",
                            "message": "BusinessType not found"
                }
                return Response(response)
            
        
    def post(self, request):
            try:
            # Create a new object
                serializer = BusinessTypeSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    response = {
                        "status_code": 201,
                        "status": "success",
                        "message":"BusinessType Create Successfully!",
                        "data": serializer.data
                    }
                    return Response(response)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
            except Exception as e:
                response = {
                            "status_code": 200,
                            "status": "success",
                            "message": "BusinessType not found nor created."
                }
                return Response(response)
class BusinessTypeRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, id):
        try:
            return master_mod.BusinessType.objects.get(id=id)
        except master_mod.BusinessType.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def get(self,request,id):
        instance = self.get_object(id)
        serializer = BusinessTypeSerializer(instance)
        response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"BusinessType Found Successfully!",
                    "data": serializer.data
                }
        return Response(response)

    def put(self, request, pk):
        # Update an existing object
        instance = self.get_object(pk)
        serializer = BusinessTypeSerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"BusinessType updated Successfully!",
                    "data": serializer.data
                }
            return Response(response)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    def delete(self, request, id):
        instance = self.get_object(id)
        instance.delete()
        response = {
                "status_code": 204,
                "status": "success",
                "message": "BusinessType Deleted"
            }
        return Response(response)

class BrandcreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self , request):
            queryset = master_mod.Brand.objects.all()
            serializer = BrandSerializer(queryset,many=True)
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"Brand Found Successfully!",
                    "data": serializer.data
                }
            return Response(response)
        
    def post(self, request):
            # Create a new object
            serializer = BrandSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                response = {
                    "status_code": 201,
                    "status": "success",
                    "message":"Brand Create Successfully!",
                    "data": serializer.data
                }
                return Response(response)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class BrandRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, id):
        try:
            return master_mod.Brand.objects.get(id=id)
        except master_mod.BusinessType.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def get(self,request,id):
        instance = self.get_object(id)
        serializer = BrandSerializer(instance)
        response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"Brand Found Successfully!",
                    "data": serializer.data
                }
        return Response(response)

    def put(self, request, pk):
        # Update an existing object
        instance = self.get_object(pk)
        serializer = BrandSerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"Brand updated Successfully!",
                    "data": serializer.data
                }
            return Response(response)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    def delete(self, request, id):
        instance = self.get_object(id)
        instance.delete()
        response = {
                "status_code": 204,
                "status": "success",
                "message": "Brand Deleted"
            }
        return Response(response)
class IndustrycreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self , request):
        try:
            queryset =Industry.objects.all()
            serializer = IndustrySerializer(queryset,many= True)
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"Industry Found Successfully!",
                    "data": serializer.data
                }
            return Response(response)
        except Exception as e:
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message": "Industry not found nor created."
        }
            return Response(response)
        
    def post(self, request):
        try:
        # Create a new object
            serializer = IndustrySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                response = {
                    "status_code": 201,
                    "status": "success",
                    "message":"Industry Create Successfully!",
                    "data": serializer.data
                }
                return Response(response)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message": "Industry not found nor created."
        }
            return Response(response)
        
class IndustryRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, id):
        try:
            return master_mod.Industry.objects.get(id=id)
        except master_mod.Industry.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def get(self,request,id):
        instance = self.get_object(id)
        serializer = IndustrySerializer(instance)
        response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"Industry Found Successfully!",
                    "data": serializer.data
                }
        return Response(response)

    def put(self, request, pk):
        # Update an existing object
        instance = self.get_object(pk)
        serializer = IndustrySerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"Industry updated Successfully!",
                    "data": serializer.data
                }
            return Response(response)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    def delete(self, request, id):
        instance = self.get_object(id)
        instance.delete()
        response = {
                "status_code": 204,
                "status": "success",
                "message": "Industry Deleted"
            }
        return Response(response)

class ProductTypecreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self , request):
        try:
            queryset = master_mod.ProductType.objects.all()
            serializer = ProductTypeSerializer(queryset,many= True)
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"ProductType Found Successfully!",
                    "data": serializer.data
                }
            return Response(response)
        except Exception as e:
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message": "ProductType not found nor created."
                     }
            return Response(response)
            
    def post(self, request):
        try:
        # Create a new object
            serializer = ProductTypeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                response = {
                    "status_code": 201,
                    "status": "success",
                    "message":"ProductType Create Successfully!",
                    "data": serializer.data
                }
                return Response(response)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message": "ProductType not found nor created."
                    }
            return Response(response)
            
class ProductTypeRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, id):
        try:
            return master_mod.ProductType.objects.get(id=id)
        except master_mod.ProductType.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def get(self,request,id):
        instance = self.get_object(id)
        serializer = ProductTypeSerializer(instance)
        response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"ProductType Found Successfully!",
                    "data": serializer.data
                }
        return Response(response)

    def put(self, request, pk):
        # Update an existing object
        instance = self.get_object(pk)
        serializer = ProductTypeSerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"ProductType updated Successfully!",
                    "data": serializer.data
                }
            return Response(response)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    def delete(self, request, id):
        instance = self.get_object(id)
        instance.delete()
        response = {
                "status_code": 204,
                "status": "success",
                "message": "ProductType Deleted"
            }
        return Response(response)

class SizecreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self , request):
        try:
            queryset = master_mod.Size.objects.all()
            serializer = SizeSerializer(queryset,many= True)
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"Size Found Successfully!",
                    "data": serializer.data
                }
            return Response(response)
        except Exception as e:
            response = {
                        "status_code": 200,
                        "status": "success",
                        "message": "Size not found nor created."
            }
            return Response(response)
    def post(self, request):
        try:
        # Create a new object
            serializer = SizeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                response = {
                    "status_code": 201,
                    "status": "success",
                    "message":"Size Create Successfully!",
                    "data": serializer.data
                }
                return Response(response)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response = {
                        "status_code": 200,
                        "status": "success",
                        "message": "Size not found nor created."
            }
            return Response(response)

class SizeRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, id):
        try:
            return master_mod.Size.objects.get(id=id)
        except master_mod.Size.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND


    def get(self,request,id):
        instance = self.get_object(id)
        serializer = SizeSerializer(instance)
        response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"Size Found Successfully!",
                    "data": serializer.data
                }
        return Response(response)

    def put(self, request, pk):
        # Update an existing object
        instance = self.get_object(pk)
        serializer = BusinessTypeSerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {
                    "status_code": 200,
                    "status": "success",
                    "message":"Size updated Successfully!",
                    "data": serializer.data
                }
            return Response(response)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    def delete(self, request, id):
        instance = self.get_object(id)
        instance.delete()
        response = {
                "status_code": 204,
                "status": "success",
                "message": "Size Deleted"
            }
        return Response(response)
