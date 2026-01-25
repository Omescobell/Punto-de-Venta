from django.db import models
from django.urls import reverse
from django.db.models.functions import ExtractWeek
from django.utils import timezone
from datetime import timedelta
import calendar

class Customer(models.Model):
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    birth_date = models.DateField()
    is_frequent = models.BooleanField(default=False)
    current_points = models.IntegerField(default=0)

    def update_frequent_status(self):
        """
        Verifica si el cliente compró en TODAS las semanas del mes anterior.
        Si cumple, se vuelve frecuente. Si no, pierde el estatus.
        """
        today = timezone.now().date()
        
        #Calcular el rango del mes anterios
        first_day_current_month = today.replace(day=1)
        last_day_prev_month = first_day_current_month - timedelta(days=1)
        first_day_prev_month = last_day_prev_month.replace(day=1)

        #Obtener todas las semanas distintas donde hubo compras en ese rango, filtramos por ventas pagadas
        weeks_with_purchases = (
            self.orders.filter(
                created_at__date__gte=first_day_prev_month,
                created_at__date__lte=last_day_prev_month,
                status='PAID' 
            )
            .annotate(week_num=ExtractWeek('created_at'))
            .values_list('week_num', flat=True)
            .distinct()
        )
        purchased_weeks_count = len(weeks_with_purchases)

        total_weeks_in_month = len(calendar.monthcalendar(first_day_prev_month.year, first_day_prev_month.month))

        is_eligible = purchased_weeks_count == total_weeks_in_month

        if self.is_frequent != is_eligible:
            self.is_frequent = is_eligible
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