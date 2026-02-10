from django.db import models, transaction
from django.urls import reverse
from django.db.models.functions import ExtractWeek
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.db.models import F

class Customer(models.Model):
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    birth_date = models.DateField()
    is_frequent = models.BooleanField(default=False)
    current_points = models.IntegerField(default=0)
    last_status_check = models.DateField(null=True, blank=True)
    last_birthday_discount_year = models.IntegerField(null=True, blank=True)

    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('2000.00'))
    credit_used = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    @property
    def available_credit(self):
        """
        Calcula cuánto crédito puede usar AHORA.
        Regla: Solo clientes frecuentes tienen acceso al crédito.
        """
        if not self.is_frequent:
            return Decimal('0.00')
        return self.credit_limit - self.credit_used

    def charge_credit(self, amount, order=None, description="Compra a crédito"):
        """
        Intenta cobrar usando el crédito de la tienda.
        """
        amount = Decimal(str(amount))
        
        if not self.is_frequent:
            raise ValidationError("El cliente no es frecuente, no tiene acceso a crédito.")
            
        if amount > self.available_credit:
            raise ValidationError(f"Crédito insuficiente. Disponible: ${self.available_credit}")

        # Crear transacción y actualizar saldo
        self.credit_used += amount
        self.save()

        CreditTransaction.objects.create(
            customer=self,
            amount=amount,
            transaction_type='CHARGE',
            description=description,
            order=order
        )

    def pay_off_credit(self, amount, description="Abono a deuda"):
        """
        El cliente paga su deuda (abona al crédito).
        """
        amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValidationError("El monto del abono debe ser positivo.")

        # Actualizar saldo (no puede ser menor a 0)
        self.credit_used = max(Decimal('0.00'), self.credit_used - amount)
        self.save()

        CreditTransaction.objects.create(
            customer=self,
            amount=amount,
            transaction_type='PAYMENT',
            description=description
        )

    @property
    def is_birthday(self):
        """Verifica si hoy es el cumpleaños del cliente (mes y día)"""
        today = timezone.now().date()
        return (self.birth_date.month == today.month and 
                self.birth_date.day == today.day)

    def can_receive_birthday_discount(self):
        """Verifica si es su cumple y si NO ha usado el descuento este año"""
        current_year = timezone.now().year
        return (self.is_birthday and 
                self.last_birthday_discount_year != current_year)

    def update_frequent_status(self):
        """
        Método público principal: Orquesta la validación del estatus de cliente frecuente.
        """
        today = timezone.now().date()

        if self._status_already_checked(today):
            return self.is_frequent

        start_date, end_date = self._get_previous_month_range(today)

        total_weeks_in_month = self._get_iso_weeks_in_range(start_date, end_date)
        weeks_with_purchases = self._get_purchased_weeks(start_date, end_date)

        is_eligible = len(weeks_with_purchases) >= len(total_weeks_in_month)

        self._save_new_status(is_eligible, today)

        return self.is_frequent

    def _status_already_checked(self, today):
        """Verifica si la revisión ya se hizo en el mes y año actual."""
        if not self.last_status_check:
            return False
            
        return (self.last_status_check.month == today.month and 
                self.last_status_check.year == today.year)

    def _get_previous_month_range(self, today):
        """Retorna tupla (fecha_inicio, fecha_fin) del mes anterior."""
        first_day_current = today.replace(day=1)
        last_day_prev = first_day_current - timedelta(days=1)
        first_day_prev = last_day_prev.replace(day=1)
        return first_day_prev, last_day_prev

    def _get_iso_weeks_in_range(self, start_date, end_date):
        """Devuelve un set con los números de semana ISO contenidos en el rango."""
        weeks = set()
        current = start_date
        while current <= end_date:
            weeks.add(current.isocalendar()[1])
            current += timedelta(days=1)
        return weeks

    def _get_purchased_weeks(self, start_date, end_date):
        """Devuelve un set de semanas donde hubo órdenes pagadas."""
        order_dates = (
            self.orders.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
                status='PAID'
            )
            .values_list('created_at', flat=True)
        )
        # Convertimos cada timestamp a su número de semana
        return {dt.isocalendar()[1] for dt in order_dates}

    def _save_new_status(self, is_eligible, check_date):
        """Actualiza el estado solo si cambió o si necesitamos actualizar la fecha de revisión."""
        if self.is_frequent != is_eligible or self.last_status_check != check_date:
            self.is_frequent = is_eligible
            self.last_status_check = check_date
            self.save(update_fields=['is_frequent', 'last_status_check'])

    def accrue_points_from_order(self, order, payment_method, total_amount):
        """
        Calcula y asigna puntos basados en una compra.
        Valida el método de pago y actualiza el estatus.
        """
        VALID_PAYMENT_METHODS = ['CASH', 'CARD']
        
        if payment_method not in VALID_PAYMENT_METHODS:
            return


        points_earned = round(Decimal(total_amount) * Decimal(0.01))

        if points_earned > 0: 

            with transaction.atomic():
                PointsTransaction.objects.create(
                    customer=self,
                    amount=points_earned,
                    transaction_type='EARN',
                    order=order,
                    description=f"Puntos compra {order.ticket_folio}"
                )

                self.current_points = F('current_points') + points_earned
                self.save()
                
                self.refresh_from_db()

                self.update_frequent_status()
    
    class Meta:
        db_table = 'CUSTOMERS'

    def get_absolute_url(self):
        return reverse("customer_detail", kwargs={"pk": self.pk})
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class PointsTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('EARN', 'Ganancia por compra'),
        ('REDEEM', 'Canjeo de puntos'),
        ('ADJUSTMENT', 'Ajuste manual'),
        ('EXPIRED', 'Expiración de puntos'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField() 
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True) 
    
    order = models.ForeignKey('orders.Order', null=True, blank=True, on_delete=models.SET_NULL) 
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} - {self.amount} ({self.transaction_type})"

class CreditTransaction(models.Model):
    """
    Historial financiero del crédito del cliente.
    Es vital para auditoría: saber cuándo se endeudó y cuándo pagó.
    """
    TRANSACTION_TYPES = [
        ('CHARGE', 'Cargo (Compra)'),     
        ('PAYMENT', 'Abono (Pago)'),       
        ('LIMIT_CHANGE', 'Cambio de Límite'), 
        ('ADJUSTMENT', 'Ajuste Manual'),   
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='credit_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True)
    
    # Vinculamos a la orden si el movimiento fue una compra
    order = models.ForeignKey('orders.Order', null=True, blank=True, on_delete=models.SET_NULL)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} - ${self.amount} ({self.transaction_type})"