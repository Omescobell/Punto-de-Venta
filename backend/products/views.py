from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend 
from rest_framework.decorators import action
from .models import Product, Promotion
from .serializers import ProductSerializer, PromotionSerializer
from .permissions import IsAdminOrOwner 
from django.db import transaction
from django.db.models import F


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminOrOwner()]
        return [permissions.IsAuthenticated()]


    #/api/products/{id}/reserve/
    @action(detail=True, methods=['post'], url_path='reserve')
    def manage_reservation(self, request, pk=None):
        product = self.get_object()
        
        amount = request.data.get('amount')
        if amount is None:
            return Response(
                {"error": "Field 'amount' is required (integer)."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = int(amount)
        except ValueError:
            return Response({"error": "Amount must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            #Bloqueamos mientras actualizamos
            product = Product.objects.select_for_update().get(pk=pk)

            new_reserved = product.reserved_quantity + amount

            if new_reserved < 0:
                return Response(
                    {"error": "Cannot release more items than reserved."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if new_reserved > product.current_stock:
                return Response(
                    {
                        "error": "Insufficient stock.", 
                        "available": product.current_stock - product.reserved_quantity
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            product.reserved_quantity = F('reserved_quantity') + amount
            product.save()
            
            product.refresh_from_db()

        return Response({
            "status": "success",
            "product": product.name,
            "reserved_quantity": product.reserved_quantity,
            "available_to_sell": product.current_stock - product.reserved_quantity
        }, status=status.HTTP_200_OK)

class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrOwner()]
        
        return [permissions.IsAuthenticated()]

    #/api/promotions/?product=1
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']