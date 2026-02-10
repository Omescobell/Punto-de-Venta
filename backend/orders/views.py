from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Order
from .serializers import OrderSerializer, OrderPaymentSerializer, OrderCancelSerializer
from .permissions import IsAdminOrOwner

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().prefetch_related('items').order_by('-created_at')
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminOrOwner()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'pay':
            return OrderPaymentSerializer
        if self.action == 'cancel':
            return OrderCancelSerializer
        return OrderSerializer

    @action(detail=True, methods=['post'], url_path='pay')
    def pay(self, request, pk=None):
        """
        Recibe la petición, valida con el serializer y ejecuta el pago.
        """
        order = self.get_object()

        serializer = OrderPaymentSerializer(
            data=request.data, 
            context={'order': order}
        )


        serializer.is_valid(raise_exception=True)

        order_pagada = serializer.process_payment()

        return Response(
            OrderSerializer(order_pagada).data, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Endpoint para cancelar una orden PENDING.
        Ruta: POST /api/orders/{id}/cancel/
        """
        order = self.get_object()
        
        serializer = self.get_serializer(order, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'Order cancelled', 
                'detail': f'La orden {order.id} fue cancelada y el stock restaurado.'
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)