from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta

from products.models import Product, Promotion
from suppliers.models import Supplier
from customers.models import Customer, PointsTransaction
from .models import Order

User = get_user_model()

class BaseOrderTestCase(APITestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username='vendedor', email='seller@test.com', password='pass', role='EMPLOYEE'
        )
        self.customer = Customer.objects.create(
            first_name="Cliente", last_name="Fiel", phone_number="555", email="c@test.com", birth_date="1990-01-01"
        )
        self.supplier = Supplier.objects.create(name="Prov", phone_number="123", rfc="ABC")
        
        self.product = Product.objects.create(
            name="Producto Test", sku="SKU-1", price=100.00, 
            current_stock=10, reserved_quantity=5, supplier=self.supplier, tax_rate='0.00'
        )

        self.promotion = Promotion.objects.create(
            name="Desc 10%", description="Test", discount_percent=10.00,
            start_date=date.today() - timedelta(days=1), end_date=date.today() + timedelta(days=365), 
            target_audience="ALL", product=self.product, is_active=True
        )

        self.list_url = reverse('order-list')
        self.client.force_authenticate(user=self.seller)

    def _get_pay_url(self, order_id):
        return reverse('order-pay', kwargs={'pk': order_id})

    def _disable_promotions(self):
        self.promotion.is_active = False
        self.promotion.save()

    def _set_no_birthday(self):
        self.customer.birth_date = date.today() - timedelta(days=180)
        self.customer.save()


class OrderUnitTests(BaseOrderTestCase):

    def test_order_calculates_iva_correctly(self):
        """Verifica el algoritmo matemático del IVA. Base 100 + 16% IVA = 116."""
        product_iva = Product.objects.create(
            name="Producto IVA", sku="IVA-16", price=Decimal('100.00'), 
            tax_rate='16.00', current_stock=10, supplier=self.supplier
        )
        response = self.client.post(self.list_url, {
            "customer": self.customer.id,
            "items": [{"product_id": product_iva.id, "quantity": 1}]
        }, format='json')
        
        order = Order.objects.get(id=response.data['id'])
        self.assertEqual(order.subtotal, Decimal('100.00'))
        self.assertEqual(order.total_tax, Decimal('16.00'))
        self.assertEqual(order.final_amount, Decimal('116.00'))

    def test_birthday_discount_applied_at_creation(self):
        """Verifica la lógica de cálculo del 10% de descuento por cumpleaños."""
        self._disable_promotions()
        self.customer.birth_date = timezone.now().date().replace(year=1990)
        self.customer.last_birthday_discount_year = None 
        self.customer.save()

        response = self.client.post(self.list_url, {
            "customer": self.customer.id, "items": [{"product_id": self.product.id, "quantity": 1}]
        }, format='json')
        
        order = Order.objects.get(id=response.data['id'])
        self.assertEqual(order.final_amount, Decimal('90.00')) 
        self.assertTrue(order.is_birthday_discount_applied)

    def test_birthday_discount_reduces_tax_liability(self):
        """Verifica la combinación de algoritmos: Descuento reduce base gravable."""
        self._disable_promotions()
        self.customer.birth_date = timezone.now().date().replace(year=1990)
        self.customer.last_birthday_discount_year = None
        self.customer.save()

        product_iva = Product.objects.create(
            name="Producto Con IVA", sku="IVA-TEST", price=Decimal('100.00'), 
            tax_rate=Decimal('16.00'), current_stock=10, supplier=self.supplier
        )

        response = self.client.post(self.list_url, {
            "customer": self.customer.id, "items": [{"product_id": product_iva.id, "quantity": 1}]
        }, format='json')
        
        order = Order.objects.get(id=response.data['id'])
        self.assertEqual(order.total_tax, Decimal('14.40')) # 16% de 90
        self.assertEqual(order.final_amount, Decimal('104.40'))

class OrderIntegrationTests(BaseOrderTestCase):

    def test_atomic_transaction_integrity(self):
        """Si un producto falla (stock), la relación con DB debe hacer rollback completo."""
        product_2 = Product.objects.create(name="Prod 2", sku="SKU-2", price=50, current_stock=1, supplier=self.supplier)
        response = self.client.post(self.list_url, {
            "customer": self.customer.id,
            "items": [{"product_id": self.product.id, "quantity": 1}, {"product_id": product_2.id, "quantity": 5}]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 10) # No interactuó con el stock final
        self.assertEqual(Order.objects.count(), 0)

    def test_cancel_pending_order_restores_stock(self):
        """Prueba la interfaz bidireccional: Cancelar orden -> Restaurar stock en Producto."""
        self._disable_promotions()
        res_create = self.client.post(self.list_url, {"items": [{"product_id": self.product.id, "quantity": 2}]}, format='json')
        order_id = res_create.data['id']

        self.client.post(reverse('order-cancel', kwargs={'pk': order_id}))
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 10) 


class OrderFunctionalTests(BaseOrderTestCase):

    def setUp(self):
        super().setUp()
        self._disable_promotions()
        res_create = self.client.post(self.list_url, {"customer": self.customer.id, "items": [{"product_id": self.product.id, "quantity": 1}]}, format='json')
        self.order_id = res_create.data['id']
        self.pay_url = self._get_pay_url(self.order_id)

    def test_create_order_without_items(self):
        """Falla funcional: Requerimiento de que no se puede crear orden vacía."""
        response = self.client.post(self.list_url, {"customer": self.customer.id, "items": []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_insufficient_stock(self):
        """Falla funcional: Requerimiento de stock físico suficiente."""
        response = self.client.post(self.list_url, {"customer": self.customer.id, "items": [{"product_id": self.product.id, "quantity": 20}]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pay_with_points_insufficient_funds(self):
        """Falla funcional: Requerimiento de saldo suficiente (Puntos parciales)."""
        self.customer.current_points = 50 
        self.customer.save()
        res_pay = self.client.post(self.pay_url, {"payment_method": "LOYALTY_POINTS"}, format='json')
        self.assertEqual(res_pay.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pay_with_points_zero_balance(self):
        """Falla funcional: Requerimiento de saldo suficiente (Cero Puntos)."""
        self.customer.loyalty_points = Decimal('0.00')
        self.customer.save()
        res_pay = self.client.post(self.pay_url, {"payment_method": "POINTS"}, format='json')
        self.assertEqual(res_pay.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pay_with_store_credit_fail_not_frequent(self):
        """Falla funcional: Requerimiento de exclusividad para clientes frecuentes."""
        self.customer.is_frequent = False
        self.customer.save()
        res_pay = self.client.post(self.pay_url, {"payment_method": "STORE_CREDIT"}, format='json')
        self.assertEqual(res_pay.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pay_with_credit_exceeds_limit(self):
        """Falla funcional: Requerimiento de no exceder límite de crédito."""
        self.customer.is_frequent = True
        self.customer.credit_limit = Decimal('50.00')
        self.customer.save()
        res_pay = self.client.post(self.pay_url, {"payment_method": "CREDIT"}, format='json')
        self.assertEqual(res_pay.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_pay_already_paid_order(self):
        """Falla funcional: Evitar doble cobro."""
        self.client.post(self.pay_url, {"payment_method": "CASH"}, format='json')
        res_pay_2 = self.client.post(self.pay_url, {"payment_method": "CARD"}, format='json')
        self.assertEqual(res_pay_2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_cancel_paid_order(self):
        """Falla funcional: No cancelar órdenes concretadas."""
        self.client.post(self.pay_url, {"payment_method": "CASH"}, format='json')
        res_cancel = self.client.post(reverse('order-cancel', kwargs={'pk': self.order_id}))
        self.assertEqual(res_cancel.status_code, status.HTTP_400_BAD_REQUEST)


class OrderSystemTests(BaseOrderTestCase):

    def setUp(self):
        super().setUp()
        self._disable_promotions()
        self._set_no_birthday()

    def test_anonymous_sale_flow(self):
        """Flujo de sistema: Compra de un cliente sin registrar."""
        res_create = self.client.post(self.list_url, {"items": [{"product_id": self.product.id, "quantity": 1}]}, format='json')
        order_id = res_create.data['id']
        order = Order.objects.get(id=order_id)
        
        self.assertIsNone(order.customer)
        res_pay = self.client.post(self._get_pay_url(order_id), {"payment_method": "CASH"}, format='json')
        self.assertEqual(res_pay.status_code, status.HTTP_200_OK)
        self.assertFalse(PointsTransaction.objects.filter(order=order).exists())

    def test_pay_with_points_success_flow(self):
        """Flujo de sistema: Cobro deduciendo puntos."""
        self.customer.current_points = 500
        self.customer.save()
        res_create = self.client.post(self.list_url, {"customer": self.customer.id, "items": [{"product_id": self.product.id, "quantity": 1}]}, format='json')
        order_id = res_create.data['id']

        res_pay = self.client.post(self._get_pay_url(order_id), {"payment_method": "LOYALTY_POINTS"}, format='json')
        self.assertEqual(res_pay.status_code, status.HTTP_200_OK)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_points, 400)

    def test_pay_with_store_credit_success_flow(self):
        """Flujo de sistema: Cobro con crédito de tienda."""
        self.customer.is_frequent = True
        self.customer.credit_limit = Decimal('2000.00')
        self.customer.save()
        res_create = self.client.post(self.list_url, {"customer": self.customer.id, "items": [{"product_id": self.product.id, "quantity": 1}]}, format='json')
        order_id = res_create.data['id']

        res_pay = self.client.post(self._get_pay_url(order_id), {"payment_method": "STORE_CREDIT"}, format='json')
        self.assertEqual(res_pay.status_code, status.HTTP_200_OK)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.available_credit, Decimal('1900.00'))


class OrderAcceptanceTests(BaseOrderTestCase):

    def test_complete_happy_path_sale_and_rewards(self):
        """
        Validación del sistema completo:
        1. Crea orden (Aplica promo automática 100 -> 90).
        2. Reduce stock.
        3. Paga en efectivo con éxito.
        4. Genera beneficios (Puntos de lealtad al cliente).
        """
        self._set_no_birthday()

        # 1. Creación
        create_data = {"customer": self.customer.id, "items": [{"product_id": self.product.id, "quantity": 2}]}
        res_create = self.client.post(self.list_url, create_data, format='json')
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        order_id = res_create.data['id']
        
        # 2. Validación de sistema en PENDING
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, 'PENDING')
        self.assertEqual(order.final_amount, Decimal('180.00')) # 90 * 2
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 8) 

        # 3. Pago
        pay_url = self._get_pay_url(order_id)
        res_pay = self.client.post(pay_url, {"payment_method": "CASH"}, format='json')
        self.assertEqual(res_pay.status_code, status.HTTP_200_OK)
        
        # 4. Beneficios y Cierre
        order.refresh_from_db()
        self.assertEqual(order.status, 'PAID')

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_points, 2) 