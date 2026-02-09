from rest_framework import serializers
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import Order, OrderItems
from products.models import Product, Promotion
from customers.models import PointsTransaction
from decimal import Decimal
from datetime import date

POINT_VALUE = Decimal("1.00")

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
            'id',
            'product_id',      
            'quantity', 
            'promotion_id',    
            'product_name', 
            'unit_price', 
            'promotion_name', 
            'discount_amount', 
            'amount',       
            'tax_amount'
        ]
        
        read_only_fields = [
            'product_name', 
            'unit_price', 
            'promotion_name', 
            'discount_amount', 
            'amount',      
            'tax_amount'
        ]
    

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True) 
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    points_to_use = serializers.IntegerField(write_only=True, required=False, default=0)
    credit_amount_to_use = serializers.DecimalField(
        write_only=True, required=False, default=Decimal(0.00), max_digits=10, decimal_places=2
    )

    class Meta:
        model = Order
        fields = [
            'id', 'ticket_folio', 'created_at', 'payment_method', 'status', 
            'seller_name', 'customer', 'customer_name', 
            'subtotal', 'total_tax', 'final_amount', 
            'discount_applied', 'money_saved_total',
            'points_used', 'store_credit_used',
            'credit_amount_to_use','points_to_use',
            'items' 
        ]
        read_only_fields = ['id', 'ticket_folio', 'created_at', 'subtotal', 'total_taxes', 'final_amount', 'status', 'points_used', 'store_credit_used']

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Validaciones básicas de items
        if not data.get('items') or len(data['items']) == 0:
            raise serializers.ValidationError({"items": "No se puede crear una orden sin productos."})

        customer = data.get('customer')
        payment_method = data.get('payment_method')
        items = data.get('items')

        if payment_method == 'LOYALTY_POINTS':
            if not customer: raise serializers.ValidationError("Se requiere cliente para Puntos.")
            if customer.current_points <= 0: raise serializers.ValidationError("Sin puntos disponibles.")
            
        if payment_method == 'STORE_CREDIT':
            if not customer: raise serializers.ValidationError("Se requiere cliente para Crédito.")
            if not customer.is_frequent: raise serializers.ValidationError("Cliente no frecuente.")
            if customer.available_credit <= 0: raise serializers.ValidationError("Sin crédito disponible.")

        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        points_to_use = validated_data.pop('points_to_use', 0)
        credit_amount = validated_data.pop('credit_amount_to_use', Decimal('0.00'))
        payment_method = validated_data.get('payment_method')
        user = self.context['request'].user
        
        with transaction.atomic():
            order = Order.objects.create(seller=user, **validated_data)

            accumulated_subtotal_base = Decimal("0.00") 
            accumulated_taxes = Decimal("0.00")         
            accumulated_savings = Decimal("0.00")       
            
            #* PROCESAMIENTO DE PRODUCTOS
            for item_data in items_data:
                product = item_data['product']
                quantity = item_data['quantity']
                promotion = item_data.get('promotion')
                
                # Bloqueo de base de datos para evitar venta de stock inexistente
                product_db = Product.objects.select_for_update().get(pk=product.pk)

                if product_db.current_stock < quantity:
                    raise serializers.ValidationError(f"Stock insuficiente para: {product_db.name}")

                unit_price_final = product_db.final_price 

                #DETERMINAR TASA DE IMPUESTO
                if product_db.tax_rate == 'EXENT':
                    tax_rate_decimal = Decimal("0.00")
                else:
                    tax_rate_decimal = Decimal(product_db.tax_rate) / Decimal("100.00")

                tax_factor = Decimal("1.00") + tax_rate_decimal

                #CALCULAR DESCUENTOS
                discount_line = Decimal("0.00")
                promo_name = None
                
                if promotion and promotion.is_active: 
                    if promotion.target_audience == 'FREQUENT_ONLY' and (not order.customer or not order.customer.is_frequent):
                        pass
                    else:
                        # El descuento se aplica sobre el precio de lista (final)
                        savings_per_unit = (unit_price_final * (promotion.discount_percent / Decimal("100")))
                        discount_line = savings_per_unit * quantity
                        accumulated_savings += discount_line
                        promo_name = promotion.name

                #CALCULO DE TOTALES DE LÍNEA
                # Total que paga el cliente por estos items = (Precio * Cant) - Descuento
                line_total_final = (unit_price_final * quantity) - discount_line
                
                #DESGLOSE DE IMPUESTOS
                line_base_amount = line_total_final / tax_factor
                line_tax_amount = line_total_final - line_base_amount
                
                # Acumulamos
                accumulated_taxes += line_tax_amount
                accumulated_subtotal_base += line_base_amount

                # Guardamos Item
                OrderItems.objects.create(
                    order=order, 
                    product=product_db, 
                    quantity=quantity,
                    product_name=product_db.name, 
                    
                    unit_price=unit_price_final,     # Precio Público
                    tax_amount=line_tax_amount,      # Impuesto histórico calculado
                    
                    promotion_name=promo_name,
                    discount_amount=discount_line, 
                    amount=line_total_final        # Cobro
                )

                # Actualizar Stock
                product_db.current_stock -= quantity
                if product_db.reserved_quantity > 0:
                    product_db.reserved_quantity = max(0, product_db.reserved_quantity - quantity)
                product_db.save()

            #* DESCUENTO CUMPLEAÑOS (GLOBAL)
            grand_total = accumulated_subtotal_base + accumulated_taxes
            
            if order.customer and order.customer.can_receive_birthday_discount():
                bday_disc_amount = grand_total * Decimal('0.10')
                
                grand_total -= bday_disc_amount
                accumulated_savings += bday_disc_amount
                
                # REAJUSTE DE IMPUESTOS:
                accumulated_taxes = accumulated_taxes * Decimal('0.90')
                accumulated_subtotal_base = accumulated_subtotal_base * Decimal('0.90')

                order.customer.last_birthday_discount_year = timezone.now().year
                order.customer.save()
                order.is_birthday_discount_applied = True

            #GUARDAR TOTALES EN LA ORDEN
            order.subtotal = accumulated_subtotal_base # Sin impuestos
            order.total_tax = accumulated_taxes      # Solo impuestos
            order.final_amount = grand_total                  # Total a pagar (Subtotal + Tax)
            order.money_saved_total = accumulated_savings
            
            if order.final_amount > 0:
                order.discount_applied = accumulated_savings / (order.final_amount + accumulated_savings)

            #* LÓGICA DE PAGO
            amount_to_pay = order.final_amount

            if payment_method == 'CASH':
                pass # Lógica futura de caja

            elif payment_method == 'CARD':
                pass # Lógica futura de terminal

            elif payment_method == 'LOYALTY_POINTS':
                points_needed = int(amount_to_pay) # 1 Punto = 1 Peso
                
                if order.customer.current_points < points_needed:
                    raise serializers.ValidationError(
                        f"Puntos insuficientes. Total: ${amount_to_pay}, Tienes: {order.customer.current_points}"
                    )
                
                PointsTransaction.objects.create(
                    customer=order.customer, amount=-points_needed, transaction_type='REDEEM',
                    order=order, description=f"Pago Ticket {order.ticket_folio}"
                )
                order.customer.current_points = F('current_points') - points_needed
                order.customer.save()
                order.points_used = points_needed

            elif payment_method == 'STORE_CREDIT':
                if amount_to_pay > order.customer.available_credit:
                    raise serializers.ValidationError(
                        f"Crédito insuficiente. Total: ${amount_to_pay}, Disponible: ${order.customer.available_credit}"
                    )
                
                try:
                    order.customer.charge_credit(
                        amount=amount_to_pay, order=order, description=f"Cargo Ticket {order.ticket_folio}"
                    )
                except Exception as e:
                    raise serializers.ValidationError(str(e))
                
                order.store_credit_used = amount_to_pay

            #* FINALIZAR Y ASIGNAR PUNTOS
            order.status = 'PAID'
            order.save()

            if payment_method in ['CASH', 'CARD'] and order.customer:
                points_earned = round(amount_to_pay * Decimal(0.01)) # 1%
                if points_earned > 0:
                    PointsTransaction.objects.create(
                        customer=order.customer, amount=points_earned, transaction_type='EARN',
                        order=order, description=f"Puntos compra {order.ticket_folio}"
                    )
                    order.customer.current_points = F('current_points') + points_earned
                    order.customer.update_frequent_status()
                    order.customer.save()

        return order