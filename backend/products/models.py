from django.db import models
from django.urls import reverse
from decimal import Decimal

class Product(models.Model):
    class TaxType(models.TextChoices):
        GENERAL = '16.00', 'Tasa General (16%)'
        FRONTIER = '8.00', 'Tasa Fronteriza (8%)'
        ZERO = '0.00', 'Tasa del 0%'
        EXEMPT = 'EXENT', 'Exento'
    
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=30, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    tax_rate = models.CharField(
        max_length=5,
        choices=TaxType.choices,
        default=TaxType.GENERAL
    )

    final_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        editable=False,
        default=0.0
    )
    current_stock = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)
    min_stock = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    supplier = models.ForeignKey(
        'suppliers.Supplier', 
        on_delete=models.PROTECT,
        related_name="products"
    )

    def save(self, *args, **kwargs):
        """Sobrescribimos el método save para calcular el precio antes de guardar"""
        if self.tax_rate == self.TaxType.EXEMPT:
            self.final_price = self.price
        else:
            tax_decimal = Decimal(self.tax_rate) / Decimal('100')
            total = self.price * (1 + tax_decimal)
            # Redondeamos a 2 decimales
            self.final_price = total.quantize(Decimal('0.01'))
        
        # Llamamos al método save original
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'PRODUCTS'

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"pk": self.pk})
    
    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"
    
class Promotion(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)
    
    TARGET_CHOICES = [
        ('ALL', 'Todos los clientes'),
        ('FREQUENT_ONLY', 'Cliente frecuente'), 
    ]
    target_audience = models.CharField(max_length=30, choices=TARGET_CHOICES)
    is_active = models.BooleanField(default=True)
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="promotions"
    )
    
    class Meta:
        db_table = 'PROMOTIONS' 

    def __str__(self):
        return f"{self.name} (-{self.discount_percent}%)"

