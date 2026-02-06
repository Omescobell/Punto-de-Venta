from rest_framework import serializers
from .models import Customer, PointsTransaction, CreditTransaction

class PointsTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsTransaction
        fields = ['id', 'amount', 'transaction_type', 'description', 'created_at']

class CreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = ['id', 'amount', 'transaction_type', 'description', 'created_at']
        read_only_fields = ['id', 'amount', 'transaction_type', 'description', 'created_at']

class CustomerSerializer(serializers.ModelSerializer):
    available_credit = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    credit_transactions = CreditTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'first_name', 'last_name', 'phone_number', 
            'email', 'is_frequent','birth_date', 'current_points', 
            'credit_limit', 'credit_used', 'available_credit',
            'credit_transactions'
        ]
        read_only_fields = ['current_points', 'credit_used', 'available_credit','is_frequent']