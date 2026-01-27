from django.db import models
from django.urls import reverse
from django.db.models.functions import ExtractWeek
from django.utils import timezone

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
        Verifica si el cliente compró en TODAS las semanas del mes anterior.
        Si cumple, se vuelve frecuente. Si no, pierde el estatus.
        """
        import calendar
        from datetime import timedelta

        today = timezone.now().date()

        #Verificamos si en este mes ya checamos si es frecuente
        if (self.last_status_check and 
            self.last_status_check.month == today.month and 
            self.last_status_check.year == today.year):
            return self.is_frequent

        # Calcular el rango del mes anterior
        first_day_current_month = today.replace(day=1)
        last_day_prev_month = first_day_current_month - timedelta(days=1)
        first_day_prev_month = last_day_prev_month.replace(day=1)

        # Obtener semanas con compras
        order_dates = (
            self.orders.filter(
                created_at__date__gte=first_day_prev_month,
                created_at__date__lte=last_day_prev_month,
                status='PAID' 
            )
            .values_list('created_at', flat=True)
        )
        purchased_weeks = {date.isocalendar()[1] for date in order_dates}

        total_weeks_in_month = len(calendar.monthcalendar(first_day_prev_month.year, first_day_prev_month.month))

        total_weeks_set = set()
        current_date = first_day_prev_month
        while current_date <= last_day_prev_month:
            total_weeks_set.add(current_date.isocalendar()[1])
            current_date += timedelta(days=1)

        is_eligible = len(purchased_weeks) >= len(total_weeks_set)

        if self.is_frequent != is_eligible or self.last_status_check != today:
            self.is_frequent = is_eligible
            self.last_status_check = today # Marcamos que ya revisamos este mes
            self.save()
            
        return self.is_frequent
    
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