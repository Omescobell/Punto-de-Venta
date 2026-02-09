from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal

class Product(models.Model):
    class TaxType(models.TextChoices):
        GENERAL = '16.00', 'Tasa General (16%)'
        FRONTIER = '8.00', 'Tasa Fronteriza (8%)'
        ZERO = '0.00', 'Tasa del 0%'
        EXEMPT = 'EXENT', 'Exento'
    
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=30, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0,help_text="Precio Base sin Impuestos")

    discounted_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,default=None,
        help_text="Precio base con descuento aplicado (antes de impuestos)"
    )

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
        """
        Calcular el precio del producto cada que se haga un cambio
        ya sea en promocion,impuesto o precio
        """
        base_amount = self.discounted_price if self.discounted_price is not None else self.price
        
        if self.tax_rate == 'EXENT':
            tax = Decimal("0.00")
        else:
            tax = base_amount * (Decimal(self.tax_rate) / Decimal("100.00"))
            
        self.final_price = base_amount + tax
        
        super().save(*args, **kwargs)
    
    def reduce_stock(self, quantity, consume_reservation=False):
        """
        Reduce el stock físico.
        :param quantity: Cantidad a restar.
        :param consume_reservation: Bool. Si es True, también resta de 'reserved_quantity'.
        """
        if quantity <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero.")

        if self.current_stock < quantity:
            raise ValidationError(f"Stock insuficiente en {self.name}. Disponible: {self.current_stock}")

        if consume_reservation:
            if self.reserved_quantity < quantity:
                raise ValidationError(f"No hay suficiente stock reservado para confirmar esta venta en {self.name}.")
            
            self.reserved_quantity -= quantity

        self.current_stock -= quantity
        self.save()

    class Meta:
        db_table = 'PRODUCTS'

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"pk": self.pk})
    
    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"
    
class Promotion(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2,validators=[MinValueValidator(0.01), MaxValueValidator(100.00)])
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

    def save(self, *args, **kwargs):
        # 1. Guardar la promoción primero 
        super().save(*args, **kwargs)
        
        self._apply_promotion_to_product()

    def _apply_promotion_to_product(self):
        """Calcula el descuento y lo INYECTA en el producto."""
        today = timezone.now().date()
        
        if self.is_active and self.start_date <= today <= self.end_date:
            discount_decimal = self.discount_percent / Decimal("100.00")
            new_price = self.product.price * (Decimal("1.00") - discount_decimal)
            
            self.product.discounted_price = new_price
        else:
            self.product.discounted_price = None

        # Al guardar el producto recalculará sus impuestos
        self.product.save()
    
    def delete(self, *args, **kwargs):
        # Si borran la promo, limpiamos el producto antes de morir
        product_ref = self.product
        super().delete(*args, **kwargs)
        self._reset_product_price(product_ref)

    @staticmethod
    def _reset_product_price(product):
        """Helper estático para limpiar un producto sin instancia de promo activa."""
        product.discounted_price = None
        product.save()
    
    @classmethod
    def deactivate_expired(cls):
        """
        Busca promociones vencidas, las apaga y LIMPIA sus productos.
        """
        now = timezone.now()
        
        # Filtramos lo que hay que limpiar: Activas pero con fecha pasada
        expired_promos = cls.objects.filter(is_active=True, end_date__lt=now)

        if not expired_promos.exists():
            return

        print(f"Detectadas {expired_promos.count()} promociones vencidas.")

        with transaction.atomic():
            for promo in expired_promos:
                # 1. Desactivar lógico
                promo.is_active = False 
                promo.save()

    @classmethod
    def check_and_activate_promotions(cls):
        """
        Revisa todas las promociones activas que sean válidas HOY
        y fuerza la actualización del precio en el producto.
        Retorna la cantidad de promociones procesadas.
        """
        today = timezone.now().date()
        
        active_promos = cls.objects.filter(
            is_active=True, 
            start_date__lte=today, 
            end_date__gte=today
        )

        count = 0
        with transaction.atomic():
            for promo in active_promos:
                promo.save()
                count += 1
        
        return count
    def __str__(self):
        return f"{self.name} (-{self.discount_percent}%)"

