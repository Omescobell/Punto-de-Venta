from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Product, Promotion
from suppliers.models import Supplier
from customers.models import Customer, PointsTransaction
from .models import Order
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

        self.product = Product.objects.create(
            name="Producto Test", sku="SKU-1", price=100.00, 
            current_stock=10, reserved_quantity=5, supplier=supplier
        )

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

        self.url = reverse('order-list') # api/orders/

    def test_successful_sale_full_flow(self):
        """
        Venta exitosa con promoción y cliente.
        Verifica: Stock, Reserva, Puntos, Descuentos y Total.
        """
        self.client.force_authenticate(user=self.seller)
        
        data = {
            "customer": self.customer.id,
            "payment_method": "CASH",
            "items": [
                {
                    "product_id": self.product.id,
                    "quantity": 2,
                    "promotion_id": self.promotion.id 
                }
            ]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        #* VERIFICACIONES
        # * Precio: 100 * 2 = 200
        # * Descuento: 10% de 100 = 10. Por 2 items = 20.
        # * Total a Pagar: 200 - 20 = 180.
        order = Order.objects.first()
        self.assertEqual(float(order.total), 180.00)
        
        item = order.items.first()
        self.assertEqual(float(item.unit_price), 100.00)
        self.assertEqual(float(item.discount_amount), 20.00)
        self.assertEqual(float(item.subtotal), 180.00)
        self.assertEqual(item.promotion_name, "Desc 10%")

    
        self.product.refresh_from_db()

        self.assertEqual(self.product.current_stock, 8)

        self.assertEqual(self.product.reserved_quantity, 3)


        self.customer.refresh_from_db()
        # Ganancia: 1% de 180 = 1.8 -> round(1.8) = 2 punto
        self.assertEqual(self.customer.current_points, 2)
        
        # Verificar que se creó la transacción de puntos
        self.assertTrue(PointsTransaction.objects.filter(order=order).exists())

    def test_sale_insufficient_stock(self):
        """
        Validación: No se puede vender más de lo que hay.
        """
        self.client.force_authenticate(user=self.seller)
        

        data = {
            "payment_method": "CASH",
            "items": [{"product_id": self.product.id, "quantity": 20}]
        }

        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Stock insuficiente", str(response.data))
        
        #No se debió crear la orden
        self.assertEqual(Order.objects.count(), 0)

    def test_sale_without_promotion(self):
        """
        Prueba venta normal sin descuentos.
        """
        self.client.force_authenticate(user=self.seller)
        
        data = {
            "payment_method": "CARD",
            "items": [{"product_id": self.product.id, "quantity": 1}]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        order = Order.objects.first()
        # 100 * 1 = 100. Sin descuento.
        self.assertEqual(float(order.total), 100.00)

    def test_stock_reservation_logic_overflow(self):
        """
        Prueba vender mas de lo reservado
        """
        self.client.force_authenticate(user=self.seller)
        
        data = {
            "payment_method": "CASH",
            "items": [{"product_id": self.product.id, "quantity": 6}]
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.product.refresh_from_db()
        # Stock: 10 - 6 = 4
        self.assertEqual(self.product.current_stock, 4)
        # Reserva: max(0, 5 - 6) = 0. NO debe ser negativo.
        self.assertEqual(self.product.reserved_quantity, 0)

    def test_atomic_transaction_integrity(self):
        """
        Prueba de Integridad: Si la orden tiene 2 productos y el SEGUNDO falla,
        el PRIMERO no debe descontarse ni guardarse.
        """
        self.client.force_authenticate(user=self.seller)
        
        product_2 = Product.objects.create(
            name="Prod 2", sku="SKU-2", price=50, current_stock=1, supplier=self.product.supplier
        )

        # Item 1: Válido (Hay stock)
        # Item 2: Inválido (Pido 5, hay 1)
        data = {
            "payment_method": "CASH",
            "items": [
                {"product_id": self.product.id, "quantity": 1}, 
                {"product_id": product_2.id, "quantity": 5}     
            ]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # El stock del producto 1 debe seguir intacto (10) aunque era válido.
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 10)
        self.assertEqual(Order.objects.count(), 0)

    def test_anonymous_sale_no_points_assigned(self):
        """
        Prueba una venta sin cliente registrado.
        Debe procesarse bien, pero NO debe generar puntos ni error.
        """
        self.client.force_authenticate(user=self.seller)
        
        data = {
            "customer": None,  
            "payment_method": "CASH",
            "items": [
                {
                    "product_id": self.product.id,
                    "quantity": 1
                }
            ]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificamos que NO se crearon transacciones de puntos
        self.assertEqual(PointsTransaction.objects.count(), 0)

    def test_inactive_promotion_does_not_apply_discount(self):
        """
        Prueba que una promoción marcada como 'is_active=False' 
        se ignore y se cobre el precio completo.
        """
        self.client.force_authenticate(user=self.seller)
        
        self.promotion.is_active = False
        self.promotion.save()

        data = {
            "customer": self.customer.id,
            "payment_method": "CASH",
            "items": [
                {
                    "product_id": self.product.id,
                    "quantity": 1,
                    "promotion_id": self.promotion.id
                }
            ]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        item = Order.objects.first().items.first()
        self.assertEqual(float(item.discount_amount), 0.00)
        self.assertIsNone(item.promotion) 

    def test_cannot_apply_promotion_of_different_product(self):
        """
        SEGURIDAD: Intentar aplicar la promo del Producto A al Producto B.
        Esto previene que alguien use un descuento de un artículo barato en uno caro.
        """
        self.client.force_authenticate(user=self.seller)
        
        product_b = Product.objects.create(
            name="TV 4K", sku="TV-001", price=10000.00, 
            current_stock=5, supplier=self.product.supplier
        )
        
        
        data = {
            "payment_method": "CASH",
            "items": [
                {
                    "product_id": product_b.id, # Compro TV
                    "quantity": 1,
                    "promotion_id": self.promotion.id #Aplico descuento de Producto Test
                }
            ]
        }


        response = self.client.post(self.url, data, format='json')
        
        # Descuento = 0
        if response.status_code == status.HTTP_201_CREATED:
            item = Order.objects.first().items.first()
            self.assertEqual(float(item.discount_amount), 0.00)

    def test_cannot_sell_zero_quantity(self):
        """Validación de datos: Cantidad 0 no permitida."""
        self.client.force_authenticate(user=self.seller)
        
        data = {
            "payment_method": "CASH",
            "items": [{"product_id": self.product.id, "quantity": 0}]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_create_empty_order(self):
        """No se puede crear un ticket sin productos."""
        self.client.force_authenticate(user=self.seller)
        
        data = {
            "customer": self.customer.id,
            "payment_method": "CASH",
            "items": [] 
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_promotion_does_not_apply(self):
        """
        Prueba una promoción que está 'is_active=True' pero cuyas fechas 
        ya pasaron. No debe aplicar descuento.
        """
        self.client.force_authenticate(user=self.seller)
        
        # Se modifica la promo para que haya vencido ayer
        from datetime import date, timedelta
        self.promotion.start_date = date.today() - timedelta(days=10)
        self.promotion.end_date = date.today() - timedelta(days=1)
        self.promotion.save()

        data = {
            "customer": self.customer.id,
            "payment_method": "CASH",
            "items": [{"product_id": self.product.id, "quantity": 1, "promotion_id": self.promotion.id}]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        item = Order.objects.first().items.first()
        # Se ignora la promocion
        self.assertEqual(float(item.discount_amount), 0.00)
        self.assertIsNone(item.promotion)

    def test_frequent_only_promotion_blocked_for_normal_customer(self):
        """
        Prueba que una promo exclusiva para clientes frecuentes no aplique a normales.
        """
        self.client.force_authenticate(user=self.seller)
        
        self.promotion.target_audience = 'FREQUENT_ONLY'
        self.promotion.save()
        
        self.customer.is_frequent = False
        self.customer.save()

        data = {
            "customer": self.customer.id, # Cliente normal
            "payment_method": "CASH",
            "items": [{"product_id": self.product.id, "quantity": 1, "promotion_id": self.promotion.id}]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        item = Order.objects.first().items.first()
        self.assertEqual(float(item.discount_amount), 0.00)

    def test_frequent_only_promotion_blocked_for_anonymous_sale(self):
        """
        Prueba que una promo VIP no aplique si no hay cliente asignado.
        """
        self.client.force_authenticate(user=self.seller)
        
        self.promotion.target_audience = 'FREQUENT_ONLY'
        self.promotion.save()

        data = {
            "customer": None, # Anónimo
            "payment_method": "CASH",
            "items": [{"product_id": self.product.id, "quantity": 1, "promotion_id": self.promotion.id}]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        item = Order.objects.first().items.first()
        self.assertEqual(float(item.discount_amount), 0.00)

    def test_non_existent_product_fails(self):
        """
        Validación de Integridad: Enviar un ID de producto que no existe.
        DRF debería atrapar esto antes de llegar a nuestra lógica.
        """
        self.client.force_authenticate(user=self.seller)
        
        data = {
            "payment_method": "CASH",
            "items": [{"product_id": 99999, "quantity": 1}]
        }

        response = self.client.post(self.url, data, format='json')
        
        # DRF lanza 400 Bad Request automático en el campo product_id
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product_id', str(response.data))

    def test_non_existent_customer_fails(self):
        """
        Validación de Integridad: Enviar un cliente que no existe.
        """
        self.client.force_authenticate(user=self.seller)
        
        data = {
            "customer": 99999, 
            "payment_method": "CASH",
            "items": [{"product_id": self.product.id, "quantity": 1}]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('customer', str(response.data))

    def test_cannot_sell_negative_quantity(self):
        """
        SEGURIDAD CRÍTICA: Impedir cantidades negativas.
        Si esto pasara, el stock aumentaría en lugar de bajar.
        """
        self.client.force_authenticate(user=self.seller)
        
        data = {
            "payment_method": "CASH",
            "items": [{"product_id": self.product.id, "quantity": -5}]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Confirmamos que el error viene de quantity
        self.assertIn("La cantidad debe ser al menos 1", str(response.data))

    def test_price_snapshot_integrity(self):
        """
        CONTABILIDAD: Si cambio el precio del producto DESPUÉS de venderlo,
        la orden vieja debe conservar el precio original (Snapshot).
        """
        self.client.force_authenticate(user=self.seller)
        
        # 1. Vendo a precio original ($100)
        data = {
            "payment_method": "CASH",
            "items": [{"product_id": self.product.id, "quantity": 1}]
        }
        self.client.post(self.url, data, format='json')
        order = Order.objects.first()
        item = order.items.first()
        
        # 2. Subo el precio del producto a $500
        self.product.price = 500.00
        self.product.save()
        
        # 3. Verifico que la orden siga en $100
        item.refresh_from_db()
        self.assertEqual(float(item.unit_price), 100.00) # NO debe ser 500
        self.assertEqual(float(item.subtotal), 100.00)

    def test_100_percent_discount_logic(self):
        """
        Prueba límite: Un producto gratis (100% descuento).
        El total debe ser 0, no negativo ni error.
        """
        self.client.force_authenticate(user=self.seller)
        
        # Creo promo del 100%
        promo_free = Promotion.objects.create(
            name="Gratis", discount_percent=100.00,
            start_date=date.today(), end_date=date.today(),
            target_audience="ALL", product=self.product, is_active=True
        )

        data = {
            "customer": self.customer.id,
            "payment_method": "CASH",
            "items": [
                {"product_id": self.product.id, "quantity": 1, "promotion_id": promo_free.id}
            ]
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        order = Order.objects.first()
        # Total debe ser 0
        self.assertEqual(float(order.total), 0.00)
        
        # Puntos: 1% de 0 es 0. No debe haber transacción de puntos.
        self.assertEqual(PointsTransaction.objects.count(), 0)
