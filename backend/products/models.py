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
    promo_requires_frequent_customer = models.BooleanField(
        default=False,
        help_text="Si está activo, solo aplica para clientes marcados como frecuentes."
    )
    active_promotion = models.ForeignKey(
        'products.Promotion', null=True, blank=True, on_delete=models.SET_NULL, related_name='active_on_products'
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

    def _calculate_taxed_price(self, amount):
        """
        Recibe un monto base y le aplica la lógica de impuestos del producto.
        Retorna: Decimal con el monto final.
        """
        if amount is None:
            return Decimal("0.00")

        if self.tax_rate == 'EXENT':
            return Decimal(amount)
        
        tax_multiplier = Decimal(self.tax_rate) / Decimal("100.00")
        
        return Decimal(amount) * (Decimal("1.00") + tax_multiplier)
    
    def save(self, *args, **kwargs):
        """
        Calcular el precio del producto cada que se haga un cambio
        ya sea en promocion,impuesto o precio
        """
        base_amount = self.discounted_price if self.discounted_price is not None else self.price
        
        self.final_price = self._calculate_taxed_price(base_amount)
        
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
    
    def get_dynamic_price(self, customer=None):
        """
        Calcula el precio real de venta al momento.
        Retorna: (precio_base_reporte, precio_final_cobrar, nombre_promocion)
        """
        #NO HAY PROMOCIÓN
        if self.discounted_price is None:
            return self.price, self.final_price, None

        promo_name = self.active_promotion.name if self.active_promotion else "Oferta"

        #PROMOCION CLIENTE FRECUENTE
        if self.promo_requires_frequent_customer:
            if customer and customer.is_frequent:
                return self.discounted_price,self.final_price, promo_name
            else:
                final_price_normal = self._calculate_taxed_price(self.price)
                return self.price, final_price_normal, None

        #PROMOCIÓN GENERAL
        return self.discounted_price, self.final_price, promo_name

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

    def sync_product_price(self):
        """
        Orquestador principal: Decide si aplicar o quitar la promoción
        basado en su validez actual.
        """
        if self.is_valid_today():
            self._apply_promotion()
        else:
            self._remove_promotion()

    def is_valid_today(self):
        """Retorna True si la promoción está activa y dentro del rango de fechas hoy."""
        today = timezone.now().date()
        return self.is_active and (self.start_date <= today <= self.end_date)

    def _calculate_discounted_price(self):
        """Calcula matemáticamente el precio con descuento."""
        discount_factor = Decimal(self.discount_percent) / Decimal("100.00")
        return Decimal(self.product.price) * (Decimal("1.00") - discount_factor)

    def _apply_promotion(self):
        """Inyecta los datos de la promoción en el producto."""
        new_price = self._calculate_discounted_price()
        
        self.product.discounted_price = new_price
        self.product.active_promotion = self
        
        # Mapeo de target_audience a booleano
        self.product.promo_requires_frequent_customer = (self.target_audience == 'FREQUENT_ONLY')
        
        self.product.save()

    def _remove_promotion(self):
        """Limpia los datos del producto SOLO si esta es la promoción activa."""
        if self.product.active_promotion_id == self.pk:
            self.product.discounted_price = None
            self.product.active_promotion = None
            self.product.promo_requires_frequent_customer = False
            
            self.product.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.sync_product_price()

    def delete(self, *args, **kwargs):
        # Si borran la promo, limpiamos el producto antes de que desaparezca la instancia
        if self.product.active_promotion_id == self.pk:
            self.product.discounted_price = None
            self.product.active_promotion = None
            self.product.requires_frequent_customer = False
            self.product.save()
            
        super().delete(*args, **kwargs)
    
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

