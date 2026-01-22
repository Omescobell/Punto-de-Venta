from rest_framework import serializers
from .models import Customer, PointsTransaction

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'email', 'birth_date', 'is_frequent', 'current_points']
        extra_kwargs = {
            'id': {'read_only': True},
            'is_frequent': {'read_only': True},
            'current_points': {'read_only': True}
        }

class PointsTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsTransaction
        fields = ['id', 'amount', 'transaction_type', 'description', 'created_at']