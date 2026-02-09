from rest_framework import serializers
from datetime import timedelta
from .models import Product, Promotion

class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'

    def validate(self, attrs):
        data = super().validate(attrs) 
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        product = attrs.get('product')

        if self.instance:
            start_date = start_date or self.instance.start_date
            end_date = end_date or self.instance.end_date
            product = product or self.instance.product

        if product and start_date and end_date:
            conflict = Promotion.objects.filter(
                product=product,
                is_active=True,
                start_date__lte=end_date,
                end_date__gte=start_date
            )

            if self.instance:
                conflict = conflict.exclude(pk=self.instance.pk)

            if conflict.exists():
                existing_promo = conflict.first() 

                suggested_end_before = existing_promo.start_date - timedelta(days=1)
                suggested_start_after = existing_promo.end_date + timedelta(days=1)

                raise serializers.ValidationError({
                    "non_field_errors": [
                        f"El rango choca con la promoción '{existing_promo.name}' "
                        f"({existing_promo.start_date} al {existing_promo.end_date}).",
                        f"Sugerencia: Intenta terminar antes del {suggested_end_before} "
                        f"o empezar después del {suggested_start_after}."
                    ]
                })
            
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError({
                    "end_date": "La fecha de finalización debe ser posterior a la fecha de inicio."
                })

        return data

class ProductSerializer(serializers.ModelSerializer):
    promotions = PromotionSerializer(many=True, read_only=True)

    final_price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    
    tax_rate_display = serializers.CharField(
        source='get_tax_rate_display', 
        read_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'price', 'tax_rate', 
            'tax_rate_display', 'final_price', 'current_stock', 
            'min_stock', 'supplier', 'updated_at', 'promotions'
        ]

    