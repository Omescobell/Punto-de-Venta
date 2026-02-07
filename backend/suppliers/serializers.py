from rest_framework import serializers
from .models import Supplier

class SupplierSerializer(serializers.ModelSerializer):
    class Meta :
        model = Supplier
        fields = ['id','name','phone_number','contact_person','rfc','tax_address']
        extra_kwargs = {
            'id': {'read_only': True}
        }