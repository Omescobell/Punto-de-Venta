from rest_framework import serializers
from django.db import transaction
from django.db.models import F
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError 
from .models import Order, OrderItems
from products.models import Product, Promotion
from customers.models import PointsTransaction
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
import math

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
    seller_name = serializers.ReadOnlyField(source='seller.username')
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'ticket_folio', 'created_at', 'payment_method', 'status','seller',
            'seller_name', 'customer', 'customer_name', 
            'subtotal', 'total_tax', 'final_amount', 
            'discount_applied', 'money_saved_total',
            'points_used', 'store_credit_used',
            'items' 
        ]
        read_only_fields = ['id', 'ticket_folio', 'created_at', 
                            'subtotal', 'total_tax', 'final_amount', 
                            'status', 'points_used', 'store_credit_used']
        
    def get_customer_name(self, obj):
        if obj.customer:
            return f"{obj.customer.first_name} {obj.customer.last_name}"
        return "Cliente General"
    
    def validate(self, attrs):
        if not attrs.get('items'):
            raise serializers.ValidationError({"items": "La orden debe tener al menos un producto."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_payload = validated_data.pop('items')
        user = self.context['request'].user

        Promotion.deactivate_expired()
        Promotion.check_and_activate_promotions()
        
        order = Order.objects.create(
            seller=user, 
            status='PENDING', 
            **validated_data
        )

        #* Crear Items y Calcular Totales Base (Precio + Impuestos normales)
        totals = self._create_items_and_calculate_totals(order, items_payload)

        #* Aplicar Descuento Cumpleaños (Si aplica)
        totals = self._apply_birthday_logic(order, totals)

        # Guardar totales finales en la Orden
        order.subtotal = totals['subtotal']
        order.total_tax = totals['tax']
        order.final_amount = totals['final_amount']
        order.money_saved_total = totals['savings']
        order.save()

        return order

    def _create_items_and_calculate_totals(self, order, items_data):
        accumulated = {
            'subtotal': Decimal("0.00"),
            'tax': Decimal("0.00"),
            'final_amount': Decimal("0.00"),
            'savings': Decimal("0.00")
        }

        customer = order.customer

        for item in items_data:
            product = item['product']
            quantity = item['quantity']

            try:
                product_db = Product.objects.select_for_update().get(pk=product.pk)
                product_db.reduce_stock(quantity, consume_reservation=False) 
            except Exception as e:
                raise serializers.ValidationError(f"Error de stock: {str(e)}")

            selling_base_price, selling_final_price, promo_name = product_db.get_dynamic_price(customer)

            line_subtotal = selling_base_price * quantity
            unit_tax = selling_final_price - selling_base_price
            line_tax = unit_tax * quantity

            unit_saving = product_db.price - selling_base_price
            line_discount = unit_saving * quantity
            
            if line_discount < 0:
                line_discount = Decimal("0.00")

            OrderItems.objects.create(
                order=order,
                product=product_db,
                quantity=quantity,
                product_name=product_db.name,
                unit_price=selling_base_price,        # Precio Base Unitario
                amount=line_subtotal,         # Subtotal de la línea (Base)
                tax_amount=line_tax,          # IVA calculado
                discount_amount=line_discount, # Ahorro del producto
                promotion_name=promo_name
            )

            accumulated['subtotal'] += line_subtotal
            accumulated['tax'] += line_tax
            accumulated['savings'] += line_discount
            accumulated['final_amount'] += (line_subtotal + line_tax)

        return accumulated


    def _calculate_tax_breakdown(self, product, base_amount):
        """
        Calcula el impuesto basado en el monto base.
        Maneja tax_rate como entero/decimal (ej: 16.00 para 16%).
        """
        tax_rate_decimal = product.tax_rate / Decimal('100.00')
        tax_amount = base_amount * tax_rate_decimal
        
        return base_amount, tax_amount

    def _apply_birthday_logic(self, order, totals):
        """
        Aplica descuento de cumpleaños (10%).
        LÓGICA: Reducimos Subtotal y Tax en un 10% directamente.
        """
        if not order.customer or not order.customer.can_receive_birthday_discount():
            return totals

        pay_factor = Decimal('0.90')

        original_final_amount = totals['final_amount']

        totals['subtotal'] = totals['subtotal'] * pay_factor
        
        # Si Tax era 16 -> Ahora es 14.40 (16 * 0.9)
        totals['tax'] = totals['tax'] * pay_factor

        # 90 + 14.40 = 104.40
        totals['final_amount'] = totals['subtotal'] + totals['tax']

        money_saved = original_final_amount - totals['final_amount']

        totals['savings'] += money_saved
        order.is_birthday_discount_applied = True
        order.money_saved_total = money_saved
        
        order.customer.last_birthday_discount_year = timezone.now().year
        order.customer.save(update_fields=['last_birthday_discount_year'])
        
        return totals

class OrderPaymentSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_CHOICES)
    amount_received = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, min_value=Decimal('0.00')
    )

    def validate(self, attrs):
        """
        Orquestador de validaciones. Delega la lógica específica a métodos privados.
        """
        order = self.context['order']
        method = attrs.get('payment_method')

        self._validate_order_status(order)

        if method == 'LOYALTY_POINTS':
            self._validate_loyalty_points(order)
        
        elif method == 'STORE_CREDIT':
            self._validate_store_credit(order)
        
        elif method == 'CARD':
            pass #Logica futura

        return attrs

    def _validate_order_status(self, order):
        if order.status == 'PAID':
            raise serializers.ValidationError(_("Esta orden ya ha sido pagada previamente."))
        if order.status == 'CANCELLED':
            raise serializers.ValidationError(_("No se puede pagar una orden cancelada."))

    def _validate_loyalty_points(self, order):
        """Valida si el cliente tiene puntos suficientes para cubrir el total."""
        if not order.customer:
            raise serializers.ValidationError(
                {"payment_method": _("El pago con Puntos requiere un cliente asignado.")}
            )

        # Regla: 1 peso = 1 punto (redondeado hacia arriba)
        points_needed = math.ceil(order.final_amount)
        
        if order.customer.current_points < points_needed:
            raise serializers.ValidationError({
                "payment_method": [
                    f"Saldo de puntos insuficiente. "
                    f"Total: ${order.final_amount} (Requiere {points_needed} pts). "
                    f"Disponible: {order.customer.current_points} pts."
                ]
            })

    def _validate_store_credit(self, order):
        """Valida reglas de crédito: cliente frecuente y límite disponible."""
        if not order.customer:
            raise serializers.ValidationError(
                {"payment_method": _("El pago con Crédito requiere un cliente asignado.")}
            )

        if not order.customer.is_frequent:
            raise serializers.ValidationError(
                {"payment_method": _("El crédito en tienda es exclusivo para Clientes Frecuentes.")}
            )

        if order.customer.available_credit < order.final_amount:
            raise serializers.ValidationError({
                "payment_method": [
                    f"Línea de crédito excedida. "
                    f"Total a pagar: ${order.final_amount}. "
                    f"Crédito disponible: ${order.customer.available_credit}."
                ]
            })

    @transaction.atomic
    def process_payment(self):
        """
        Ejecuta el cobro y actualiza la orden. 
        Asume que validate() ya pasó exitosamente.
        """
        order = self.context['order']
        method = self.validated_data['payment_method']
        
        if method == 'LOYALTY_POINTS':
            self._process_points_deduction(order)
        elif method == 'STORE_CREDIT':
            self._process_credit_charge(order)
        
        order.payment_method = method
        order.status = 'PAID'
        order.save()
        
        if order.customer:
            order.customer.accrue_points_from_order(
                order=order,
                payment_method=method,
                total_amount=order.final_amount
            )

        return order

    def _process_points_deduction(self, order):
        points_needed = math.ceil(order.final_amount)
        
        PointsTransaction.objects.create(
            customer=order.customer,
            amount=-points_needed,
            transaction_type='REDEEM',
            order=order,
            description=f"Pago Ticket #{order.ticket_folio}"
        )
        # Actualización atómica
        order.customer.current_points = models.F('current_points') - points_needed
        order.customer.save()
        
        order.points_used = points_needed

    def _process_credit_charge(self, order):
        order.customer.charge_credit(
            amount=order.final_amount,
            order=order,
            description=f"Pago Ticket #{order.ticket_folio}"
        )
        order.store_credit_used = order.final_amount

class OrderCancelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']
        read_only_fields = ['status']

    def validate(self, attrs):
        # REGLA DE ORO: Solo cancelar si NO se ha pagado
        if self.instance.status != 'PENDING':
            raise serializers.ValidationError(
                "No se puede cancelar una orden que ya fue pagada. Debe realizar una devolución."
            )
        return attrs

    def save(self, **kwargs):
        order = self.instance
        
        with transaction.atomic():
            order_items = order.items.all()
            for item in order_items:
                product = item.product
                product.current_stock = F('current_stock') + item.quantity
                product.save()

            order.status = 'CANCELLED'
            order.save()
            
        return order