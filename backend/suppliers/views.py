from django.shortcuts import render
from rest_framework import status,viewsets, permissions
from .models import Supplier
from .serializers import SupplierSerializer
from .permissions import IsAdminOrOwner

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated] 

    def get_permissions(self):
        return [IsAdminOrOwner()]
