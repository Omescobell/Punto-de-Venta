from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Product, Promotion
from suppliers.models import Supplier
from customers.models import Customer, PointsTransaction
from .models import Order
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()

class SaleProcessTests(APITestCase):

    def setUp(self):
        self.seller = User.objects.create_user(
            username='vendedor', email='seller@test.com', password='pass', role='EMPLOYEE'
        )

        self.customer = Customer.objects.create(
            first_name="Cliente", last_name="Fiel", phone_number="555", email="c@test.com", birth_date="1990-01-01"
        )

        supplier = Supplier.objects.create(name="Prov", phone_number="123", rfc="ABC")
        
        # Producto base: Precio $100
        self.product = Product.objects.create(
            name="Producto Test", sku="SKU-1", price=100.00, 
            current_stock=10, reserved_quantity=5, supplier=supplier, tax_rate='0.00'
        )

        # Esta promoción se aplica automáticamente en todos los tests si no se desactiva.
        # Reduce el precio a $90.
        self.promotion = Promotion.objects.create(
            name="Desc 10%", 
            description="Test", 
            discount_percent=10.00,
            start_date=date.today() - timedelta(days=1), 
            end_date=date.today() + timedelta(days=365), 
            target_audience="ALL", 
            product=self.product, 
            is_active=True
        )

        self.list_url = reverse('order-list')

    def _get_pay_url(self, order_id):
        return reverse('order-pay', kwargs={'pk': order_id})


    # ! TESTS DE CREACIÓN (Cálculos y Stock)

    def test_create_order_calculations_pending_state(self):
        """
        Prueba que al crear la orden:
        1. Se aplica la promoción del setup ($100 -> $90).
        2. El stock se reduce.
        """
        self.client.force_authenticate(user=self.seller)
        
        # Aseguramos que NO es su cumpleaños para aislar el test de promoción
        self.customer.birth_date = date.today() - timedelta(days=180)
        self.customer.save()

        data = {
            "customer": self.customer.id,
            "items": [
                {
                    "product_id": self.product.id,
                    "quantity": 2
                    # No enviamos promotion_id explícito, el sistema debería detectarlo
                }
            ]
        }

        # Precio unitario con promo: 90. Cantidad: 2. Total: 180. Ahorro: 20.
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        order = Order.objects.get(id=response.data['id'])
        
        self.assertEqual(order.status, 'PENDING')
        self.assertEqual(order.final_amount, Decimal('180.00'))
        self.assertEqual(order.money_saved_total, Decimal('20.00'))

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 8) 

    def test_create_order_insufficient_stock(self):
        self.client.force_authenticate(user=self.seller)
        
        data = {
            "customer": self.customer.id,
            "items": [{"product_id": self.product.id, "quantity": 20}] 
        }

        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_calculates_iva_correctly(self):
        """Verifica cálculos de IVA. Base 100 + 16% IVA = 116 Total."""
        self.client.force_authenticate(user=self.seller)
        
        # Creamos un producto nuevo SIN promoción asociada
        product_iva = Product.objects.create(
            name="Producto IVA", 
            sku="IVA-16", 
            price=Decimal('100.00'), 
            tax_rate='16.00',
            current_stock=10, 
            supplier=self.product.supplier
        )

        data = {
            "customer": self.customer.id,
            "items": [{"product_id": product_iva.id, "quantity": 1}]
        }

        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        order = Order.objects.get(id=response.data['id'])
        
        self.assertEqual(order.subtotal, Decimal('100.00')) # Base
        self.assertEqual(order.total_tax, Decimal('16.00')) # IVA
        self.assertEqual(order.final_amount, Decimal('116.00')) # Total

    def test_birthday_discount_applied_at_creation(self):
        """El descuento de cumpleaños se calcula al crear la orden."""
        self.client.force_authenticate(user=self.seller)

        # 1. Desactivamos la promoción del Setup para que el precio base sea $100
        # Si no, sería $90 - 10% = $81. Queremos probar $100 - 10% = $90.
        self.promotion.is_active = False
        self.promotion.save()

        # 2. Configurar cumpleaños HOY
        today = date.today()
        self.customer.birth_date = today.replace(year=1990)
        self.customer.last_birthday_discount_year = None 
        self.customer.save()

        data = {
            "customer": self.customer.id,
            "items": [{"product_id": self.product.id, "quantity": 1}]
        }

        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        order = Order.objects.get(id=response.data['id'])
        
        # $100 - 10% (Cumple) = $90
        self.assertEqual(order.final_amount, Decimal('90.00'))
        self.assertTrue(order.is_birthday_discount_applied)
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.last_birthday_discount_year, today.year)

    def test_birthday_discount_reduces_tax_liability(self):
        """
        Prueba Fiscal: Descuento de cumpleaños reduce la base gravable.
        Base 100 -> Descuento 10% -> Base 90.
        IVA 16% sobre 90 = 14.40.
        Total = 104.40.
        """
        self.client.force_authenticate(user=self.seller)

        # 1. Configurar Cumpleaños
        today = date.today()
        self.customer.birth_date = today.replace(year=1990)
        self.customer.last_birthday_discount_year = None
        self.customer.save()

        # 2. Producto con IVA (Sin promoción asociada, precio puro 100)
        product_iva = Product.objects.create(
            name="Producto Con IVA", 
            sku="IVA-TEST", 
            price=Decimal('100.00'), 
            tax_rate=Decimal('16.00'),
            current_stock=10, 
            supplier=self.product.supplier
        )

        data = {
            "customer": self.customer.id,
            "items": [{"product_id": product_iva.id, "quantity": 1}]
        }

        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        order = Order.objects.get(id=response.data['id'])

        expected_tax = Decimal('14.40') 
        self.assertEqual(order.total_tax, expected_tax, 
            f"El impuesto debería ser {expected_tax} (16% de 90), fue {order.total_tax}")

        expected_total = Decimal('104.40')
        self.assertEqual(order.final_amount, expected_total)

    def test_atomic_transaction_integrity(self):
        """Si un producto falla (stock), no se crea nada."""
        self.client.force_authenticate(user=self.seller)
        
        product_2 = Product.objects.create(
            name="Prod 2", sku="SKU-2", price=50, current_stock=1, supplier=self.product.supplier
        )

        data = {
            "customer": self.customer.id,
            "items": [
                {"product_id": self.product.id, "quantity": 1}, 
                {"product_id": product_2.id, "quantity": 5}     # Fail
            ]
        }

        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 10)
        self.assertEqual(Order.objects.count(), 0)


    # ! TESTS DE PAGO (Flujo Completo)

    def test_pay_with_cash_success(self):
        self.client.force_authenticate(user=self.seller)

        # Quitamos cumple y promo para cálculos simples
        self.customer.birth_date = date.today() - timedelta(days=180)
        self.customer.save()
        self.promotion.is_active = False
        self.promotion.save()

        # 1. Crear Orden ($100 * 2 = $200)
        create_data = {
            "customer": self.customer.id,
            "items": [{"product_id": self.product.id, "quantity": 2}]
        }
        res_create = self.client.post(self.list_url, create_data, format='json')
        order_id = res_create.data['id']
        
        # 2. Pagar
        pay_url = self._get_pay_url(order_id)
        pay_data = {"payment_method": "CASH"}
        
        res_pay = self.client.post(pay_url, pay_data, format='json')
        self.assertEqual(res_pay.status_code, status.HTTP_200_OK)
        
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, 'PAID')

        # Puntos: 1% de 200 = 2 puntos
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_points, 2)

    def test_pay_with_points_success(self):
        self.client.force_authenticate(user=self.seller)
        
        # 1. Limpieza de entorno (Sin cumple, sin promo)
        self.customer.birth_date = date.today() - timedelta(days=180) 
        self.customer.save()
        self.promotion.is_active = False
        self.promotion.save()

        # Damos puntos suficientes (500)
        self.customer.current_points = 500
        self.customer.save()

        # 2. Crear Orden ($100)
        create_data = {
            "customer": self.customer.id,
            "items": [{"product_id": self.product.id, "quantity": 1}]
        }
        res_create = self.client.post(self.list_url, create_data, format='json')
        order_id = res_create.data['id']

        # 3. Pagar con Puntos
        pay_url = self._get_pay_url(order_id)
        pay_data = {"payment_method": "LOYALTY_POINTS"}
        
        res_pay = self.client.post(pay_url, pay_data, format='json')
        self.assertEqual(res_pay.status_code, status.HTTP_200_OK)

        order = Order.objects.get(id=order_id)
        self.assertEqual(order.points_used, 100)
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_points, 400) # 500 - 100

    def test_pay_with_points_insufficient_funds(self):
        self.client.force_authenticate(user=self.seller)
        self.customer.birth_date = date.today() - timedelta(days=180)
        self.customer.current_points = 50 # Insuficientes
        self.customer.save()
        self.promotion.is_active = False
        self.promotion.save()

        create_data = {
            "customer": self.customer.id,
            "items": [{"product_id": self.product.id, "quantity": 1}]
        }
        res_create = self.client.post(self.list_url, create_data, format='json')
        order_id = res_create.data['id']

        pay_url = self._get_pay_url(order_id)
        res_pay = self.client.post(pay_url, {"payment_method": "LOYALTY_POINTS"}, format='json')
        
        self.assertEqual(res_pay.status_code, status.HTTP_400_BAD_REQUEST)
        
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, 'PENDING')

    def test_pay_with_store_credit_success(self):
        self.client.force_authenticate(user=self.seller)
        self.promotion.is_active = False # Sin promo para que cueste 100 exactos
        self.promotion.save()
        
        self.customer.is_frequent = True
        self.customer.credit_limit = Decimal('2000.00')
        self.customer.save()

        create_data = {
            "customer": self.customer.id,
            "items": [{"product_id": self.product.id, "quantity": 1}]
        }
        res_create = self.client.post(self.list_url, create_data, format='json')
        order_id = res_create.data['id']

        pay_url = self._get_pay_url(order_id)
        res_pay = self.client.post(pay_url, {"payment_method": "STORE_CREDIT"}, format='json')
        self.assertEqual(res_pay.status_code, status.HTTP_200_OK)

        order = Order.objects.get(id=order_id)
        self.assertEqual(order.store_credit_used, Decimal('100.00'))
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.available_credit, Decimal('1900.00'))

    def test_pay_with_store_credit_fail_not_frequent(self):
        self.client.force_authenticate(user=self.seller)
        self.customer.is_frequent = False
        self.customer.save()

        # AQUÍ ESTABA EL KEYERROR: Faltaba format='json'
        res_create = self.client.post(self.list_url, {
            "customer": self.customer.id,
            "items": [{"product_id": self.product.id, "quantity": 1}]
        }, format='json')
        
        order_id = res_create.data['id']

        pay_url = self._get_pay_url(order_id)
        res_pay = self.client.post(pay_url, {"payment_method": "STORE_CREDIT"}, format='json')
        
        self.assertEqual(res_pay.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_pay_already_paid_order(self):
        self.client.force_authenticate(user=self.seller)

        # AQUÍ ESTABA EL KEYERROR: Faltaba format='json'
        res_create = self.client.post(self.list_url, {
            "customer": self.customer.id,
            "items": [{"product_id": self.product.id, "quantity": 1}]
        }, format='json')
        
        order_id = res_create.data['id']
        pay_url = self._get_pay_url(order_id)

        # Pagar 1
        self.client.post(pay_url, {"payment_method": "CASH"}, format='json')
        
        # Pagar 2
        res_pay_2 = self.client.post(pay_url, {"payment_method": "CARD"}, format='json')
        
        self.assertEqual(res_pay_2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ya ha sido pagada", str(res_pay_2.data))
    
    def test_anonymous_sale_flow(self):
        """
        Venta anónima: Se crea, se paga (Cash), pero NO genera puntos
        porque no hay cliente asociado.
        """
        self.client.force_authenticate(user=self.seller)
        
        # Desactivamos la promo global para simplificar cálculos
        self.promotion.is_active = False
        self.promotion.save()

        # 1. Crear sin enviar 'customer'
        data = {
            "items": [{"product_id": self.product.id, "quantity": 1}],
            "customer": None # O simplemente no enviarlo
        }
        
        res_create = self.client.post(self.list_url, data, format='json')
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        
        order_id = res_create.data['id']
        order = Order.objects.get(id=order_id)
        
        self.assertIsNone(order.customer)
        self.assertEqual(order.final_amount, Decimal('100.00'))

        # 2. Pagar
        pay_url = self._get_pay_url(order_id)
        res_pay = self.client.post(pay_url, {"payment_method": "CASH"}, format='json')
        self.assertEqual(res_pay.status_code, status.HTTP_200_OK)

        # 3. Verificar que NO hay transacción de puntos (ni error)
        # Como no hay cliente, no debe haber movimiento de puntos
        self.assertFalse(PointsTransaction.objects.filter(order=order).exists())
    
    def test_create_order_without_items(self):
        """No se puede crear una orden con la lista de items vacía."""
        self.client.force_authenticate(user=self.seller)
        
        data = {
            "customer": self.customer.id,
            "items": []
        }

        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('items', response.data)
    
    def test_pay_with_points_insufficient_balance(self):
        """
        Verifica que falle el pago si el cliente intenta pagar con Puntos
        pero no tiene saldo suficiente para cubrir el total.
        """
        self.client.force_authenticate(user=self.seller)

        # 1. Aseguramos que el cliente tenga 0 puntos
        self.customer.loyalty_points = Decimal('0.00')
        self.customer.save()

        # 2. Crear Orden (Monto aprox 116.00)
        res_create = self.client.post(self.list_url, {
            "customer": self.customer.id,
            "items": [{"product_id": self.product.id, "quantity": 1}]
        }, format='json')
        
        order_id = res_create.data['id']

        # 3. Intentar Pagar con PUNTOS
        pay_url = self._get_pay_url(order_id)
        res_pay = self.client.post(pay_url, {"payment_method": "POINTS"}, format='json')

        # 4. Esperamos un error 400 Bad Request
        self.assertEqual(res_pay.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Opcional: Verificar que el mensaje sea claro (ajusta el texto a tu error real)
        # self.assertIn("saldo", str(res_pay.data).lower())
    
    def test_pay_with_credit_exceeds_limit(self):
        """
        Verifica que el sistema rechace el pago con CRÉDITO si el monto de la orden
        hace que el cliente supere su límite de crédito establecido.
        """
        self.client.force_authenticate(user=self.seller)

        # 1. Configurar al cliente con un límite bajo
        # Digamos que su límite es 50.00 y no debe nada aún.
        self.customer.credit_limit = Decimal('50.00')
        self.customer.credit_used = Decimal('0.00') 
        # NOTA: Ajusta 'credit_used' o 'current_balance' al nombre real de tu campo en el modelo Customer
        self.customer.save()

        # 2. Crear una Orden que supere el límite
        # El producto vale 100 + 16 IVA = 116.00
        # 116.00 > 50.00 (Límite) -> Debe fallar
        res_create = self.client.post(self.list_url, {
            "customer": self.customer.id,
            "items": [{"product_id": self.product.id, "quantity": 1}]
        }, format='json')
        
        order_id = res_create.data['id']

        # 3. Intentar pagar con CRÉDITO
        pay_url = self._get_pay_url(order_id)
        res_pay = self.client.post(pay_url, {"payment_method": "CREDIT"}, format='json')

        # 4. Validar que falle
        self.assertEqual(res_pay.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Opcional: Verificar que el mensaje mencione el límite
        # self.assertIn("límite", str(res_pay.data).lower())
    
    def test_cancel_pending_order_restores_stock(self):
        """
        Al cancelar una orden PENDING, el stock debe regresar al inventario
        y el estado pasar a CANCELLED.
        """
        self.client.force_authenticate(user=self.seller)
        
        # 1. Stock Inicial: 10
        self.product.current_stock = 10
        self.product.save()

        # 2. Crear Orden
        res_create = self.client.post(self.list_url, {
            "items": [{"product_id": self.product.id, "quantity": 2}]
        }, format='json')
        order_id = res_create.data['id']

        # Verificar que bajó a 8
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 8)

        # 3. CANCELAR
        cancel_url = reverse('order-cancel', kwargs={'pk': order_id})
        res_cancel = self.client.post(cancel_url)
        self.assertEqual(res_cancel.status_code, status.HTTP_200_OK)

        # 4. Verificar restauración
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 10) # Volvió a 10
        
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, 'CANCELLED')
    
    def test_cannot_cancel_paid_order(self):
        """
        No se debe permitir cancelar una orden que ya tiene estatus PAID.
        """
        self.client.force_authenticate(user=self.seller)

        # 1. Crear Orden
        res_create = self.client.post(self.list_url, {
            "items": [{"product_id": self.product.id, "quantity": 1}]
        }, format='json')
        order_id = res_create.data['id']

        # 2. Pagarla
        pay_url = self._get_pay_url(order_id)
        self.client.post(pay_url, {"payment_method": "CASH"}, format='json')

        # 3. Intentar CANCELAR
        cancel_url = reverse('order-cancel', kwargs={'pk': order_id})
        res_cancel = self.client.post(cancel_url)

        # 4. Verificar Error 400
        self.assertEqual(res_cancel.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No se puede cancelar", str(res_cancel.data))