from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Customer, PointsTransaction
from .serializers import CustomerSerializer, PointsTransactionSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated] 
    #/api/customers/{id}/history/
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        customer = self.get_object() # Obtener id del cliente de la url
        
        transactions = customer.transactions.all().order_by('-created_at')
        
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = PointsTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PointsTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    # /api/customers/{id}/points/
    @action(detail=True, methods=['post'])
    def points(self, request, pk=None):
        customer = self.get_object()
        amount = request.data.get('amount')
        trans_type = request.data.get('transaction_type')
        description = request.data.get('description', '')
        order = request.data.get('order')

        if not amount or not trans_type:
            return Response(
                {"error": "Fields 'amount' and 'transaction_type' are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = int(amount)
        except ValueError:
            return Response({"error": "Amount must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            PointsTransaction.objects.create(
                customer=customer,
                amount=amount,
                transaction_type=trans_type,
                description=description,
            )

            # (Usamos F expressions para evitar condiciones de carrera si hay concurrencia)
            from django.db.models import F
            customer.current_points = F('current_points') + amount
            customer.save()
            
            customer.refresh_from_db()

        return Response({
            "status": "success",
            "new_balance": customer.current_points
        }, status=status.HTTP_201_CREATED)
    