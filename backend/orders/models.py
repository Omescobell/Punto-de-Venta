from django.db import models
from django.urls import reverse
import uuid
class Order(models.Model):
    ticket_folio = models.CharField(max_length=50, unique=True, blank=True)
    
    PAYMENT_CHOICES = [
        ('CARD', 'Tarjeta'),
        ('CASH', 'Efectivo'),
        ('STORE_CREDIT', 'Crédito Tienda'),
        ('LOYALTY_POINTS', 'Puntos'),       
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, null=True,blank=True)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,help_text="Total final con impuestos")
    is_birthday_discount_applied = models.BooleanField(default=False, help_text="Indica si se aplicó descuento de cumpleaños")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total antes de impuestos")
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total de impuestos (IVA)")
    points_used = models.IntegerField(default=0)
    store_credit_used = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    money_saved_total = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Monto total ahorrado (Suma de descuentos)"
    )
    
    STATUS_CHOICES = [
        ('PAID', 'Pagado'),
        ('PENDING', 'Pendiente'),
        ('CANCELED', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING') 
    created_at = models.DateTimeField(auto_now_add=True)
    
    customer = models.ForeignKey(
        'customers.Customer', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        related_name="orders"
    )
    seller = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name="sales"
    )

    class Meta:
        db_table = 'ORDERS'

    def save(self, *args, **kwargs):
        if not self.ticket_folio:
            self.ticket_folio = str(uuid.uuid4()).split('-')[0].upper()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("order_detail", kwargs={"pk": self.pk})
    
    def __str__(self):
        return f"{self.ticket_folio}, {self.status}"


class OrderItems(models.Model):
    quantity = models.PositiveIntegerField()
    product_name = models.CharField(max_length=200)
    promotion_name = models.CharField(max_length=50, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10,decimal_places=2)
    discount_amount = models.DecimalField (max_digits=10,decimal_places=2, default=0.00)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Monto de IVA de este ítem")
    order = models.ForeignKey(Order,
                            on_delete=models.CASCADE,
                            related_name="items")
    product = models.ForeignKey('products.Product',
                                on_delete=models.SET_NULL,
                                null=True,
                                related_name="order_items")
    promotion = models.ForeignKey('products.Promotion',
                                on_delete=models.SET_NULL,
                                null=True,
                                related_name="applied_in_orders")
    class Meta:
        db_table = 'ORDER_ITEMS'
    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
