from rest_framework import serializers
from .models import Product, Promotion

class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'

    #Fecha inicio no puede ser mayor a fecha fin
    def validate(self, attrs):
        data = super().validate(attrs) 
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if self.instance:
            start_date = start_date or self.instance.start_date
            end_date = end_date or self.instance.end_date

        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError({
                    "end_date": "La fecha de finalización debe ser posterior a la fecha de inicio."
                })

        return data

class ProductSerializer(serializers.ModelSerializer):
    promotions = PromotionSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    