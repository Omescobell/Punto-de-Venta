from rest_framework import serializers
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    class Meta :
        model = Customer
        fields = ['id','first_name','last_name','phone_number','email','birth_date','is_frequent']
        extra_kwargs = {
            'id': {'read_only': True},
            'is_frequent' : {'read_only': True}
        }