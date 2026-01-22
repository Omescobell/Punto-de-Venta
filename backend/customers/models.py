from django.db import models
from django.urls import reverse

class Customer(models.Model):
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    birth_date = models.DateField()
    is_frequent = models.BooleanField(default=False)
    current_points = models.IntegerField(default=0)

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