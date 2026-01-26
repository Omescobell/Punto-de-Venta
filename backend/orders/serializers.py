from rest_framework import serializers
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import Order, OrderItems
from products.models import Product, Promotion
from customers.models import PointsTransaction
from decimal import Decimal
from datetime import date

class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    promotion_id = serializers.PrimaryKeyRelatedField(
        queryset=Promotion.objects.all(), source='promotion', required=False, allow_null=True, write_only=True
    )
    quantity = serializers.IntegerField(
        min_value=1,
        error_messages={
            'min_value': 'La cantidad debe ser al menos 1.',
            'invalid': 'Debe ser un número entero válido.'
        }
    )

    class Meta:
        model = OrderItems
        fields = [
            'product_id', 'quantity', 'promotion_id', 
            'product_name', 'unit_price', 'promotion_name', 
            'discount_amount', 'subtotal'
        ]
        read_only_fields = ['product_name', 'unit_price', 'promotion_name', 'discount_amount', 'subtotal']
    

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True) 
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'ticket_folio', 'created_at', 
            'payment_method', 'status', 
            'seller_name', 'customer', 'customer_name', 
            'total', 'items' 
        ]
        read_only_fields = ['id', 'ticket_folio', 'created_at', 'total', 'status']

    def validate(self, attrs):
        data = super().validate(attrs) 
        if not data.get('items') or len(data['items']) == 0:
            raise serializers.ValidationError({"items": "No se puede crear una orden sin productos."})
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        with transaction.atomic():
            order = Order.objects.create(seller=user, **validated_data)
            final_ammount = 0
            total_save = Decimal("0.00")
            for item_data in items_data:
                product = item_data['product']
                quantity = item_data['quantity']
                promotion = item_data.get('promotion')

                product_db = Product.objects.select_for_update().get(pk=product.pk)

                #Validación de Stock
                if product_db.current_stock < quantity:
                    raise serializers.ValidationError(
                        f"Stock insuficiente para {product_db.name}. Disponible: {product_db.current_stock}"
                    )

                unit_price = product_db.price
                money_saved_total = Decimal("0.00")
                promo_name = None
                applied_promotion_obj= None

                if promotion:
                    if (promotion.product.id == product_db.id and 
                        promotion.is_active and 
                        (promotion.start_date <= date.today() <= promotion.end_date)):
                        
                        if promotion.target_audience == 'FREQUENT_ONLY' and (not order.customer or not order.customer.is_frequent):
                            pass 
                        else:
                            savings_per_unit = (unit_price * (promotion.discount_percent / Decimal("100")))
                            money_saved_total = savings_per_unit * quantity
                            total_save += money_saved_total
                            promo_name = promotion.name
                            applied_promotion_obj = promotion

                subtotal_line = (unit_price * quantity) - money_saved_total
                
                final_ammount += subtotal_line

                OrderItems.objects.create(
                    order=order,
                    product=product_db,
                    quantity=quantity,
                    product_name=product_db.name,
                    promotion=applied_promotion_obj,
                    promotion_name=promo_name,
                    unit_price=unit_price,
                    discount_amount=money_saved_total,
                    subtotal=subtotal_line             
                )

                #Actualización de Inventario (Stock y Reservas)
                
                product_db.current_stock -= quantity
                if product_db.reserved_quantity > 0:
                    product_db.reserved_quantity = max(0, product_db.reserved_quantity - quantity)
                
                product_db.save()

            if order.customer and order.customer.can_receive_birthday_discount():
                birthay_disccount = final_ammount * Decimal('0.10')
                total_save += birthay_disccount
                final_ammount -= birthay_disccount
                order.customer.last_birthday_discount_year = timezone.now().year
                order.customer.save()
                order.is_birthday_discount_applied = True
            total = final_ammount + total_save
            discount_applied = total_save / total
            order.final_amount = final_ammount
            order.total = total
            order.discount_applied = discount_applied
            order.save()

            #Puntos del cliente
            if order.customer:
                points_earned = round(final_ammount * Decimal(0.01))
                if points_earned > 0:
                    PointsTransaction.objects.create(
                        customer=order.customer,
                        amount=points_earned,
                        transaction_type='EARN',
                        order=order,
                        description=f"Puntos por ticket {order.ticket_folio}"
                    )
                    
                    # Actualización segura de puntos
                    order.customer.current_points = F('current_points') + points_earned

                    order.customer.update_frequent_status()
                    order.customer.save()

        return order