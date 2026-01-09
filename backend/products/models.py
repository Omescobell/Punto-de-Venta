from django.db import models
from django.urls import reverse

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=30, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    current_stock = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)
    min_stock = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    supplier = models.ForeignKey(
        'suppliers.Supplier', 
        on_delete=models.PROTECT,
        related_name="products"
    )

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"pk": self.pk})
    
    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"
    
class Promotion(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    discount_percent = models.DecimalField(max_digits=2,decimal_places=2)
    start_date = models.TimeField(null=False)
    end_date = models.TimeField(null=False)
    TARGET_CHOICES = [
        ('ALL', 'Todos los clientes'),
        ('FREQUENTY', 'Cliente frecuente'),
    ]
    target_audience = models.CharField(max_length=30,choices=TARGET_CHOICES)
    is_active = models.BooleanField()
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="promotions")
    
    def get_absolute_url(self):
        return reverse("promotion_detail", kwargs={"pk": self.pk})
    
    def __str__(self):
        return f"{self.name}"

