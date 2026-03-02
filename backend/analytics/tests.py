from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

# Importa tus modelos (ajusta las rutas según la estructura de tu proyecto)
from users.models import User
from customers.models import Customer
from products.models import Product, Promotion
from orders.models import Order, OrderItems
from suppliers.models import Supplier

class AnalyticsSalesSummaryTests(APITestCase):
    
    def setUp(self):
        """
        Configuración inicial: Creamos usuarios, proveedores, products, 
        promociones, clientes y múltiples órdenes de prueba (incluyendo
        casos fuera de rango y cancelados) para asegurar los cálculos.
        """

        #! 1. USUARIOS Y ROLES (Basado en tu README)
        self.admin_user = User.objects.create_user(
            username='admin_user', email='admin@enterprise.com', 
            password='password123', role='ADMIN'
        )
        self.owner_user = User.objects.create_user(
            username='owner_user', email='owner@enterprise.com', 
            password='password123', role='OWNER'
        )
        self.employee_user = User.objects.create_user(
            username='cajero', email='employee@pos.com', 
            password='password123', role='EMPLOYEE'
        )


        #! 2. DATOS BASE (Cliente, Proveedor, products)
        self.customer = Customer.objects.create(
            first_name="Cliente", last_name="Base", phone_number="5500000000",
            email="base@cliente.com", birth_date="1990-01-01"
        )

        self.supplier = Supplier.objects.create(
            name="Proveedor General", phone_number="123456789", rfc="ABC123456T1"
        )
        
        self.product_laptop = Product.objects.create(
            name="Laptop", sku="LAP-1", price=Decimal('1000.00'), 
            current_stock=10, reserved_quantity=0, supplier=self.supplier, tax_rate='16.00'
        )
        
        self.product_mouse = Product.objects.create(
            name="Mouse", sku="MOU-1", price=Decimal('50.00'), 
            current_stock=20, reserved_quantity=0, supplier=self.supplier, tax_rate='16.00'
        )

        #! 3. FECHAS DE CONTROL PARA PRUEBAS
        self.today = timezone.localtime(timezone.now())
        self.yesterday = self.today - timedelta(days=1)
        self.last_week = self.today - timedelta(days=7)
        self.future_date = self.today + timedelta(days=10) # Para probar cuando no hay ventas
        
        # Horas específicas para las órdenes
        self.time_10am = self.yesterday.replace(hour=10, minute=0, second=0)
        self.time_2pm = self.yesterday.replace(hour=14, minute=30, second=0)
        self.time_last_week = self.last_week.replace(hour=11, minute=0, second=0)


        #! 4. CREACIÓN DE ÓRDENES Y VENTAS

        # ORDEN 1: Ayer 10:00 AM | $1160 | CARD 
        self.order1 = Order.objects.create(
            customer=self.customer, seller=self.employee_user,
            payment_method='CARD', status='PAID', final_amount=Decimal('1160.00')
        )
        OrderItems.objects.create(
            order=self.order1, product=self.product_laptop, product_name="Laptop",
            quantity=1, unit_price=Decimal('1000.00'), amount=Decimal('1000.00'), tax_amount=Decimal('160.00')
        )

        # ORDEN 2: Ayer 2:00 PM | $116 | CASH 
        self.order2 = Order.objects.create(
            customer=self.customer, seller=self.employee_user,
            payment_method='CASH', status='PAID', final_amount=Decimal('116.00')
        )
        OrderItems.objects.create(
            order=self.order2, product=self.product_mouse, product_name="Mouse",
            quantity=2, unit_price=Decimal('50.00'), amount=Decimal('100.00'), tax_amount=Decimal('16.00')
        )

        # ORDEN 3: Ayer 2:00 PM | $1218 | CARD 
        self.order3 = Order.objects.create(
            customer=self.customer, seller=self.employee_user,
            payment_method='CARD', status='PAID', final_amount=Decimal('1218.00')
        )
        OrderItems.objects.create(
            order=self.order3, product=self.product_laptop, product_name="Laptop",
            quantity=1, unit_price=Decimal('1000.00'), amount=Decimal('1000.00'), tax_amount=Decimal('160.00')
        )
        OrderItems.objects.create(
            order=self.order3, product=self.product_mouse, product_name="Mouse",
            quantity=1, unit_price=Decimal('50.00'), amount=Decimal('50.00'), tax_amount=Decimal('8.00')
        )

        # ORDEN 4 (TRAMPA ESTATUS): Ayer | $300 | CANCELED 
        self.order_canceled = Order.objects.create(
            customer=self.customer, seller=self.employee_user,
            payment_method='CARD', status='CANCELED', final_amount=Decimal('300.00')
        )
        OrderItems.objects.create(
            order=self.order_canceled, product=self.product_laptop, product_name="Laptop",
            quantity=1, unit_price=Decimal('300.00'), amount=Decimal('300.00'), tax_amount=Decimal('48.00')
        )

        # ORDEN 5 (TRAMPA FECHA): Semana Pasada | $500 | PAID 
        self.order_out_of_range = Order.objects.create(
            customer=self.customer, seller=self.employee_user,
            payment_method='CASH', status='PAID', final_amount=Decimal('500.00')
        )
        OrderItems.objects.create(
            order=self.order_out_of_range, product=self.product_mouse, product_name="Mouse",
            quantity=10, unit_price=Decimal('50.00'), amount=Decimal('500.00'), tax_amount=Decimal('80.00')
        )

        # IMPORTANTE: Forzamos la actualización de fechas saltando el auto_now_add
        Order.objects.filter(id=self.order1.id).update(created_at=self.time_10am)
        Order.objects.filter(id=self.order2.id).update(created_at=self.time_2pm)
        Order.objects.filter(id=self.order3.id).update(created_at=self.time_2pm)
        Order.objects.filter(id=self.order_canceled.id).update(created_at=self.time_10am)
        Order.objects.filter(id=self.order_out_of_range.id).update(created_at=self.time_last_week)

        # La URL de tu viewset (ajusta a como se llame en tu urls.py, usualmente 'nombre-action')
        self.url = reverse('analytics-sales-summary')

    # ! PRUEBAS DE SEGURIDAD Y PERMISOS 

    def test_unauthenticated_access_denied(self):
        """Un usuario sin token debe recibir un 401 Unauthorized"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_access_forbidden(self):
        """Un empleado debe recibir un 403 Forbidden"""
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_allowed(self):
        """Un administrador debe poder acceder al recurso (200 OK)"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_access_allowed(self):
        """Un owner debe poder acceder al recurso (200 OK)"""
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # !PRUEBAS DE MANEJO DE FECHAS 

    def test_sales_summary_default_dates(self):
        """Si no se pasan fechas, debe usar el rango por defecto."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('general_summary', response.data)
        self.assertIn('analyzed_period', response.data)

    def test_sales_summary_invalid_date_format(self):
        """Formato incorrecto debe devolver 400."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'start_date': '01-01-2023', 'end_date': '2023-01-31'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_sales_summary_dates_without_records(self):
        """Fechas futuras o sin registros deben regresar un error con límites del sistema."""
        self.client.force_authenticate(user=self.admin_user)
        future_str = self.future_date.strftime('%Y-%m-%d')
        
        response = self.client.get(self.url, {'start_date': future_str, 'end_date': future_str})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) # O HTTP_200_OK, dependiendo de tu API
        self.assertIn('error', response.data)
        self.assertIn('first_system_record', response.data)
        self.assertIn('last_system_records', response.data)


    # ! PRUEBAS DE LÓGICA, CÁLCULOS Y EXCLUSIONES 

    def test_sales_summary_calculations(self):
        """
        Prueba los cálculos de Sum, Max, Min, promedios y agrupaciones
        garantizando que ignora las trampas (CANCELED y fuera de rango).
        """
        self.client.force_authenticate(user=self.admin_user)
        
        # Consultamos el día de ayer
        date_str = self.yesterday.strftime('%Y-%m-%d')
        response = self.client.get(self.url, {'start_date': date_str, 'end_date': date_str})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # 1. Validar Totales Generales (Solo las 3 órdenes PAID de ayer)
        resumen = data['general_summary']
        self.assertEqual(resumen['total_tickets'], 3)
        self.assertEqual(float(resumen['highest_ticket']), 1218.00)
        self.assertEqual(float(resumen['lowest_ticket']), 116.00)
        self.assertEqual(float(resumen['total_revenue']), 2494.00) # 1160 + 116 + 1218

        # 2. Validar products
        products = data['products']
        self.assertEqual(products['total_units_sold'], 5) # 2 Laptops + 3 Mouses
        self.assertEqual(products['top_product']['product_name'], 'Laptop')
        
        # 3. Validar Horas Pico
        horas = data['peak_hours']
        self.assertEqual(horas['busiest_hour']['hour'], 14) # A las 14:00 hubieron 2 tickets
        self.assertEqual(horas['busiest_hour']['ticket_count'], 2)
        
        # 4. Validar Métodos de Pago
        pagos = data['payment_methods']
        self.assertEqual(len(pagos), 2) # CARD y CASH
        
        card_stats = next(p for p in pagos if p['payment_method'] == 'CARD')
        cash_stats = next(p for p in pagos if p['payment_method'] == 'CASH')
        
        self.assertEqual(card_stats['total_sales'], 2)
        self.assertEqual(cash_stats['total_sales'], 1)

    def test_sales_summary_excludes_canceled_orders(self):
        """Verifica explícitamente que no se haya sumado la orden CANCELED de $300."""
        self.client.force_authenticate(user=self.admin_user)
        date_str = self.yesterday.strftime('%Y-%m-%d')
        response = self.client.get(self.url, {'start_date': date_str, 'end_date': date_str})
        
        self.assertEqual(float(response.data['general_summary']['total_revenue']), 2494.00)
        self.assertEqual(response.data['general_summary']['total_tickets'], 3)

    def test_sales_summary_includes_extended_date_range(self):
        """
        Al ampliar el rango, la orden PAID de la semana pasada debe sumarse,
        pero la orden CANCELED debe seguir siendo ignorada.
        """
        self.client.force_authenticate(user=self.admin_user)
        
        start_str = self.last_week.strftime('%Y-%m-%d')
        end_str = self.yesterday.strftime('%Y-%m-%d')
        
        response = self.client.get(self.url, {'start_date': start_str, 'end_date': end_str})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3 tickets PAID de ayer + 1 ticket PAID de la semana pasada = 4 tickets.
        self.assertEqual(response.data['general_summary']['total_tickets'], 4)
        
        # $2494 (ayer) + $500 (semana pasada) = $2994.00
        self.assertEqual(float(response.data['general_summary']['total_revenue']), 2994.00)


class ProductRankingTests(APITestCase):
    
    def setUp(self):
        """
        Configuración inicial para probar el ranking de products.
        Crearemos 3 products con diferentes volúmenes de venta.
        """
        # 1. Usuarios
        self.admin_user = User.objects.create_user(username='admin2', email='admin2@test.com', password='123', role='ADMIN')
        self.owner_user = User.objects.create_user(username='owner2', email='owner2@test.com', password='123', role='OWNER')
        self.employee_user = User.objects.create_user(username='emp2', email='emp2@test.com', password='123', role='EMPLOYEE')

        # 2. Cliente y Proveedor
        self.customer = Customer.objects.create(
            first_name="Cliente", last_name="Ranking", phone_number="5500000001",
            email="ranking@cliente.com", birth_date="1990-01-01"
        )
        self.supplier = Supplier.objects.create(name="Prov2", phone_number="123", rfc="XYZ")

        # 3. products
        self.product_laptop = Product.objects.create(
            name="Laptop", sku="LAP-2", price=Decimal('1000.00'), supplier=self.supplier
        )
        self.product_mouse = Product.objects.create(
            name="Mouse", sku="MOU-2", price=Decimal('50.00'), supplier=self.supplier
        )
        self.product_keyboard = Product.objects.create(
            name="Teclado", sku="KEY-2", price=Decimal('150.00'), supplier=self.supplier
        )

        # 4. Fechas
        self.today = timezone.localtime(timezone.now())
        self.yesterday = self.today - timedelta(days=1)
        self.future_date = self.today + timedelta(days=10)

        # 5. Órdenes y Ventas (Para generar el ranking)
        # Total a vender: Laptop (1 pieza), Mouse (3 piezas), Teclado (5 piezas)
        
        self.order = Order.objects.create(
            customer=self.customer, seller=self.employee_user,
            payment_method='CARD', status='PAID', final_amount=Decimal('1900.00')
        )
        Order.objects.filter(id=self.order.id).update(created_at=self.yesterday)

        # Vendemos 1 Laptop
        OrderItems.objects.create(
            order=self.order, product=self.product_laptop, product_name="Laptop",
            quantity=1, unit_price=Decimal('1000.00'), amount=Decimal('1000.00')
        )
        # Vendemos 3 Mouses
        OrderItems.objects.create(
            order=self.order, product=self.product_mouse, product_name="Mouse",
            quantity=3, unit_price=Decimal('50.00'), amount=Decimal('150.00')
        )
        # Vendemos 5 Teclados
        OrderItems.objects.create(
            order=self.order, product=self.product_keyboard, product_name="Teclado",
            quantity=5, unit_price=Decimal('150.00'), amount=Decimal('750.00')
        )

        # URL de la vista (Ajusta el basename según tu urls.py)
        self.url = reverse('analytics-product-ranking')


    # ! PRUEBAS DE SEGURIDAD 

    def test_permissions(self):
        """Verifica que solo ADMIN y OWNER tengan acceso."""
        # Unauthenticated
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Employee
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ! PRUEBAS DE CRITERIO Y LÍMITE 

    def test_ranking_default_parameters(self):
        """Si no se envían parámetros, debe devolver los 'mas' vendidos con límite de 10."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results']
        
        self.assertEqual(data['criterion'], 'most')
        self.assertEqual(data['limite_results'], 10)
        self.assertIn('most_sold', data)
        self.assertNotIn('least_sold', data)

        # El más vendido debe ser el Teclado (5 piezas), luego Mouse (3), luego Laptop (1)
        most_sold = data['most_sold']
        self.assertEqual(most_sold[0]['product_name'], 'Teclado')
        self.assertEqual(most_sold[1]['product_name'], 'Mouse')
        self.assertEqual(most_sold[2]['product_name'], 'Laptop')

    def test_ranking_least_sold(self):
        """Prueba el criterio 'menos', debe ordenar del peor al mejor."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'criterion': 'least'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        least_sold = response.data['results']['least_sold']
        
        # El menos vendido fue la Laptop (1 pieza), luego Mouse (3), luego Teclado (5)
        self.assertEqual(least_sold[0]['product_name'], 'Laptop')
        self.assertEqual(least_sold[1]['product_name'], 'Mouse')
        self.assertEqual(least_sold[2]['product_name'], 'Teclado')

    def test_ranking_ambos_con_limite(self):
        """
        Prueba el criterio 'ambos' y restringe el límite a 2.
        Debemos recibir dos listas separadas y truncadas.
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'criterion': 'both', 'limit': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results']
        
        self.assertEqual(data['limite_results'], 2)
        
        # Verificamos que las listas tengan solo 2 elementos
        self.assertEqual(len(data['most_sold']), 2)
        self.assertEqual(len(data['least_sold']), 2)
        
        # Top 2 más vendidos: Teclado, Mouse
        self.assertEqual(data['most_sold'][0]['product_name'], 'Teclado')
        
        # Top 2 menos vendidos: Laptop, Mouse
        self.assertEqual(data['least_sold'][0]['product_name'], 'Laptop')

    def test_invalid_parameters_fallback(self):
        """
        Si envían basura en los parámetros, el sistema debe sanitizar
        usando los valores por defecto sin crashear.
        """
        self.client.force_authenticate(user=self.admin_user)
        # Mandamos letras al limit y un criterio inventado
        response = self.client.get(self.url, {'criterion': 'locura', 'limit': 'texto'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results']
        
        # Debe fallback a: criterion='mas', limit=10
        self.assertEqual(data['criterion'], 'most')
        self.assertEqual(data['limite_results'], 10)

    # ! PRUEBAS DE FECHAS Y CASOS ESPECIALES 
    def test_empty_sales_in_range(self):
        """
        Si se piden fechas en las que no hay registros, el validador estricto 
        de fechas debe detener la petición en la Fase 1 y regresar 400.
        """
        self.client.force_authenticate(user=self.admin_user)
        
        # Consultamos el día de hoy (nuestras órdenes forzadas fueron ayer)
        today_str = self.today.strftime('%Y-%m-%d')
        response = self.client.get(self.url, {'start_date': today_str, 'end_date': today_str})
        # La petición es rechazada correctamente por falta de registros
        self.assertIn('error', response.data)
        self.assertIn('first_system_record', response.data)
        self.assertIn('last_system_records', response.data)
        self.assertIn('no tiene ventas en el sistema', str(response.data['error']).lower())

    def test_invalid_date_format(self):
        """Formato de fecha inválido debe ser procesado devolviendo 400."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Enviamos ambas fechas con formato incorrecto (DD-MM-YYYY)
        response = self.client.get(self.url, {'start_date': '01-01-2023', 'end_date': '31-01-2023'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], "Formato de fecha inválido. Usa YYYY-MM-DD.")

class LowStockReportTests(APITestCase):

    def setUp(self):
        # Aseguramos el rol ADMIN para no tener errores 403 de permisos
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='pass', role='ADMIN', is_superuser=True, is_staff=True
        )
        self.supplier = Supplier.objects.create(name="Prov", phone_number="123", rfc="ABC")
        self.url = reverse('analytics-low-stock') 
        self.client.force_authenticate(user=self.admin)

    # ==========================================
    # PRUEBAS DE FILTRADO
    # ==========================================
    def test_filter_by_explicit_threshold(self):
        """Regla: Filtra estrictamente por current_stock <= threshold."""
        Product.objects.create(name="Producto A", sku="SKU-1", price=100, current_stock=20, low_stock=False, supplier=self.supplier)
        Product.objects.create(name="Producto B", sku="SKU-2", price=100, current_stock=5, low_stock=False, supplier=self.supplier)

        # Pedimos umbral de 10. Solo debe traer el Producto B.
        response = self.client.get(self.url, {'threshold': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Asumiendo que tu vista devuelve la lista directamente en caso de éxito
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Producto B")

    def test_filter_by_low_stock_boolean(self):
        """Regla: Si no hay threshold, filtra donde low_stock=True."""
        Product.objects.create(name="Producto A", sku="SKU-1", price=10, current_stock=20, low_stock=False, supplier=self.supplier)
        Product.objects.create(name="Producto B", sku="SKU-2", price=10, current_stock=5, low_stock=True, supplier=self.supplier)

        # No enviamos threshold. Solo debe traer el Producto B (porque low_stock=True).
        response = self.client.get(self.url) 
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Producto B")

    # ==========================================
    # PRUEBAS DE ORDENAMIENTO Y ESTRUCTURA
    # ==========================================
    def test_results_ordering(self):
        """Regla: Ordena los resultados por -current_stock (descendente)."""
        Product.objects.create(name="Producto A", sku="SKU-1", price=100, current_stock=2, low_stock=True, supplier=self.supplier)
        Product.objects.create(name="Producto B", sku="SKU-2", price=100, current_stock=10, low_stock=True, supplier=self.supplier)
        Product.objects.create(name="Producto C", sku="SKU-3", price=100, current_stock=5, low_stock=True, supplier=self.supplier)

        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        # El orden debe ser: 10, 5, 2
        self.assertEqual(response.data[0]['current_stock'], 10)
        self.assertEqual(response.data[1]['current_stock'], 5)
        self.assertEqual(response.data[2]['current_stock'], 2)

    def test_payload_structure(self):
        """Regla: El diccionario devuelto solo contiene 'name' y 'current_stock'."""
        Product.objects.create(name="Producto A", sku="SKU-1", price=100, current_stock=5, low_stock=True, supplier=self.supplier)

        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data[0]
        self.assertEqual(list(item.keys()), ['name', 'current_stock'])

    # ==========================================
    # PRUEBAS DE MANEJO DE ERRORES / MENSAJES
    # ==========================================
    def test_empty_inventory_message(self):
        """Regla: Si no hay productos en BD, devuelve el mensaje de error correspondiente."""
        Product.objects.all().delete()
        response = self.client.get(self.url)
        
        # Asumiendo que tu vista devuelve el diccionario completo en caso de error
        self.assertFalse(response.data.get('success'))
        self.assertEqual(response.data.get('message'), "No hay productos registrados en el sistema.")

    def test_invalid_threshold_message(self):
        """Regla: Si el threshold no es numérico, devuelve error."""
        Product.objects.create(name="Producto A", sku="SKU-1", price=100, current_stock=10, low_stock=False, supplier=self.supplier)
        
        response = self.client.get(self.url, {'threshold': 'abc'})
        
        self.assertFalse(response.data.get('success'))
        self.assertEqual(response.data.get('message'), "El umbral proporcionado no es un número válido.")

class DeadInventoryReportTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='pass', role='ADMIN', is_superuser=True, is_staff=True
        )
        self.supplier = Supplier.objects.create(name="Prov", phone_number="123", rfc="ABC")
        self.customer = Customer.objects.create(
            first_name="Cliente Genérico", 
            email="test@cliente.com",
            birth_date="1990-01-01"
            )
        
        self.url = reverse('analytics-dead-inventory') 
        self.client.force_authenticate(user=self.admin)

    # --- HELPER PARA CREAR ÓRDENES DIRECTO EN BD ---
    def _create_paid_order_for_test(self, product, is_paid=True, override_date=None):
        """Crea una orden directamente en la BD saltándose la API para agilizar el test."""
        order_status = 'PAID' if is_paid else 'PENDING'
        
        # Creamos la orden con los campos mínimos que parece requerir tu modelo
        order = Order.objects.create(
            customer=self.customer,
            status=order_status
        )
        
        # 2. Le asociamos el producto (esto dispara los cálculos en tu sistema)
        OrderItems.objects.create(
            order=order,
            product=product,
            quantity=1,
            unit_price=product.price,
            amount=product.final_price
        )

        # 3. Refrescamos desde la base de datos para obtener los totales calculados solos
        order.refresh_from_db()

        # 4. Si necesitamos simular una fecha en el pasado (Django protege auto_now_add)
        if override_date:
            Order.objects.filter(id=order.id).update(created_at=override_date)
            order.refresh_from_db() # Refrescamos por si acaso          
        return order

    # ==========================================
    # MANEJO DE ERRORES Y VALIDACIONES
    # ==========================================
    def test_empty_inventory_returns_error(self):
        """Si no hay productos, devuelve el mensaje de error."""
        Product.objects.all().delete()
        response = self.client.get(self.url)
        
        self.assertFalse(response.data.get('success'))
        self.assertEqual(response.data.get('message'), "No hay productos registrados en el sistema para analizar.")
    def test_invalid_date_format_returns_error(self):
        """Si la fecha explícita es incorrecta, devuelve error."""
        Product.objects.create(name="Producto Test", sku="SKU-1", price=Decimal('100.00'), current_stock=10, supplier=self.supplier)
        
        # ¡OJO AQUÍ! Cambia 'reference_date' por la llave exacta que espera tu views.py
        response = self.client.get(self.url, {'reference_date': 'fecha-rara-123'})
        
        # Si la vista atrapa el error y lo devuelve como diccionario:
        self.assertIn("Formato de fecha", str(response.data))

    def test_all_products_sold_returns_message(self):
        """Si todos los productos se han vendido, notifica que no hay inventario muerto."""
        prod = Product.objects.create(name="Prod A", sku="SKU-1", price=Decimal('100.00'), current_stock=10, supplier=self.supplier)
        
        # Usamos nuestro helper para simular que ya se pagó
        self._create_paid_order_for_test(product=prod, is_paid=True)

        response = self.client.get(self.url)
        
        self.assertFalse(response.data.get('success'))
        self.assertEqual(response.data.get('message'), "Todos los productos han tenido ventas en este período.")

    # ==========================================
    # LÓGICA DE NEGOCIO: IDENTIFICACIÓN
    # ==========================================
    def test_identifies_dead_inventory_default_30_days(self):
        """Identifica inventario muerto usando el default de 30 días, ignorando órdenes no pagadas."""
        prod_activo = Product.objects.create(name="Producto Activo", sku="SKU-1", price=Decimal('10.00'), current_stock=5, supplier=self.supplier)
        prod_muerto = Product.objects.create(name="Producto Muerto", sku="SKU-2", price=Decimal('10.00'), current_stock=8, supplier=self.supplier)
        prod_no_pagado = Product.objects.create(name="Producto Fallido", sku="SKU-3", price=Decimal('10.00'), current_stock=12, supplier=self.supplier)

        # Solo el producto activo se paga realmente
        self._create_paid_order_for_test(product=prod_activo, is_paid=True)
        self._create_paid_order_for_test(product=prod_no_pagado, is_paid=False)

        response = self.client.get(self.url) 
        data = response.data # Obtenemos la lista directa de la respuesta
        
        # Deben regresar 2 productos (el muerto y el que no se pagó)
        self.assertEqual(len(data), 2)
        
        # Extraemos solo los nombres de la respuesta para validarlos fácilmente
        nombres_devueltos = [item['name'] for item in data]
        
        self.assertIn("Producto Muerto", nombres_devueltos)
        self.assertIn("Producto Fallido", nombres_devueltos)
        self.assertNotIn("Producto Activo", nombres_devueltos)
        
        # Validamos que devuelva la estructura exacta que mencionaste
        self.assertIn('id', data[0])
        self.assertIn('name', data[0])
        self.assertIn('current_stock', data[0])

    def test_identifies_dead_inventory_with_explicit_date(self):
        """Usa una fecha antigua explícita para buscar qué no se ha vendido desde entonces."""
        prod_vendido_hoy = Product.objects.create(name="Vendido Hoy", sku="SKU-1", price=Decimal('10.00'), current_stock=5, supplier=self.supplier)
        prod_vendido_viejo = Product.objects.create(name="Vendido Viejo", sku="SKU-2", price=Decimal('10.00'), current_stock=8, supplier=self.supplier)
        prod_muerto = Product.objects.create(name="Inventario Muerto", sku="SKU-3", price=Decimal('10.00'), current_stock=10, supplier=self.supplier)

        self._create_paid_order_for_test(product=prod_vendido_hoy, is_paid=True)

        # Simulamos que este producto se vendió hace un año
        fecha_antigua = timezone.now() - timedelta(days=365)
        self._create_paid_order_for_test(product=prod_vendido_viejo, is_paid=True, override_date=fecha_antigua)

        # Pedimos el reporte desde hace 10 días
        fecha_corte = (timezone.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        response = self.client.get(self.url, {'reference_date_str': fecha_corte})

        data = response.data # Obtenemos la lista
        
        self.assertEqual(len(data), 2)
        nombres_devueltos = [item['name'] for item in data]
        
        self.assertIn("Inventario Muerto", nombres_devueltos)
        self.assertIn("Vendido Viejo", nombres_devueltos) # Entra al reporte porque su última venta fue hace más de 10 días
        self.assertNotIn("Vendido Hoy", nombres_devueltos)

class CustomerSalesTests(APITestCase):

    def setUp(self):
        # 1. Crear usuario administrador y autenticar
        self.admin_user = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='password123'
        )
        self.client.force_authenticate(user=self.admin_user)

        # 2. Configurar la URL del endpoint
        self.url = '/api/analytics/customer-sales/'

        # 3. Crear Clientes de prueba
        self.customer_active = Customer.objects.create(
            first_name="Juan",
            last_name="Pérez",
            phone_number="5551234567", 
            email="juan@test.com",     
            birth_date="1990-05-15"
        )
        
        self.customer_inactive = Customer.objects.create(
            first_name="Ana",
            last_name="Gómez",
            phone_number="5559876543",  
            email="ana@test.com",       
            birth_date="1995-08-20"
        )
        
        # 3.5 Crear Proveedor
        self.supplier = Supplier.objects.create(
            name="Proveedor General", phone_number="123456789", rfc="ABC123456T1"
        )

        # 4. Crear Productos (El sistema les calculará el final_price con 16% IVA automáticamente)
        self.product_1 = Product.objects.create(
            sku="EDSADAS", name="Laptop", price=Decimal('1000.00'), current_stock=10, supplier=self.supplier
        )
        self.product_2 = Product.objects.create(
            sku="DASDASDSA", name="Mouse", price=Decimal('100.00'), current_stock=50, supplier=self.supplier
        )

        recent_date = timezone.now()

        # 5. Crear Orden 1 (Solo status y método de pago)
        # 5. Crear Orden 1 
        self.order_1 = Order.objects.create(
            customer=self.customer_active,
            status='PAID',
            payment_method='CARD',
        )
        
        OrderItems.objects.create(order=self.order_1, product_name=self.product_1.name, product=self.product_1, quantity=1, unit_price=self.product_1.price, amount=self.product_1.final_price)
        OrderItems.objects.create(order=self.order_1,product_name=self.product_2.name, product=self.product_2, quantity=1, unit_price=self.product_2.price, amount=self.product_2.final_price)

        # SIMULAMOS el cálculo que haría tu API de creación de órdenes
        self.order_1.final_amount = Decimal('1276.00')
        self.order_1.created_at = recent_date
        self.order_1.save()

        # 6. Crear Orden 2 
        self.order_2 = Order.objects.create(
            customer=self.customer_active,
            status='PAID',
            payment_method='CASH',
        )
        
        OrderItems.objects.create(order=self.order_2, product=self.product_2,product_name=self.product_2.name, quantity=2, unit_price=self.product_2.price, amount=self.product_2.final_price * 2)

        # SIMULAMOS el cálculo
        self.order_2.final_amount = Decimal('232.00')
        self.order_2.created_at = recent_date
        self.order_2.save()

    def test_customer_sales_success(self):
        """Prueba que devuelve las métricas correctas para un cliente con compras (con IVA incluido)."""
        response = self.client.get(self.url, {'customer_id': self.customer_active.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        
        # Validar llaves principales
        self.assertIn('customer_info', data)
        self.assertIn('analyzed_period', data)
        self.assertIn('sales_metrics', data)
        self.assertIn('top_product', data)
        
        # Validar la información del cliente
        self.assertEqual(data['customer_info']['id'], self.customer_active.id)
        self.assertEqual(data['customer_info']['first_name'], "Juan")
        self.assertEqual(data['customer_info']['last_name'], "Pérez")
        
        # Validar métricas de ventas. Tu sistema debió calcular 1508.00 (1276.00 + 232.00)
        self.assertEqual(float(data['sales_metrics']['total_spent']), 1508.00)
        self.assertEqual(data['sales_metrics']['total_tickets'], 2)
        self.assertEqual(float(data['sales_metrics']['average_ticket']), 754.00)

        # Validar el producto estrella
        self.assertEqual(data['top_product']['product_name'], "Laptop")
        self.assertEqual(float(data['top_product']['total_spent_on_product']), 1160.00)

    def test_customer_no_purchases_in_period(self):
        """Prueba que maneja correctamente a un cliente válido pero sin compras (Escenario A)."""
        response = self.client.get(self.url, {'customer_id': self.customer_inactive.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
        self.assertEqual(
            response.data['detail'], 
            "This customer made no purchases during the selected period."
        )
        self.assertEqual(response.data['customer_info']['first_name'], "Ana")

    def test_missing_customer_id(self):
        """Prueba que devuelve error 400 si no se envía el parámetro obligatorio."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], "customer_id parameter is required.")

    def test_customer_not_found(self):
        """Prueba que devuelve error 404 si el ID del cliente no existe."""
        response = self.client.get(self.url, {'customer_id': 9999})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], "Customer not registered in the system.")


class SalesVelocityTests(APITestCase):

    def setUp(self):
        # 1. Autenticación
        self.user = User.objects.create_superuser(username='admin', password='password123',email="admin@gmail.com")
        self.client.force_authenticate(user=self.user)
        
        # URL de la acción (ajusta si tu router tiene otro prefijo)
        self.url = '/api/analytics/sales-velocity/' 

        # 2. Datos Base
        self.supplier = Supplier.objects.create(name="Proveedor X", phone_number="123", rfc="XXX")
        self.customer = Customer.objects.create(first_name="Test", last_name="Customer", email="test@test.com",birth_date="2000-12-12")

        # 3. Crear Producto de Alta Rotación
        self.product_fast = Product.objects.create(
            sku="FAST123", 
            name="Laptop Gamer", 
            price=Decimal('1000.00'), 
            current_stock=100, # <--- Stock de 100
            supplier=self.supplier
        )

        # 4. Crear Producto Estancado (Sin ventas)
        self.product_slow = Product.objects.create(
            sku="SLOW123", 
            name="Mouse Viejo", 
            price=Decimal('10.00'), 
            current_stock=50, 
            supplier=self.supplier
        )

        # 5. Simular una venta hace exactamente 10 días
        now = timezone.now()
        ten_days_ago = now - timedelta(days=10)

        self.order = Order.objects.create(customer=self.customer, status='PAID', payment_method='CASH')
        
        # Vendemos 20 unidades
        OrderItems.objects.create(
            order=self.order, 
            product=self.product_fast, 
            product_name=self.product_fast.name,
            quantity=20,  # <--- 20 unidades vendidas
            unit_price=self.product_fast.price, 
            amount=self.product_fast.price * 20
        )

        # Forzamos la fecha al pasado (hace 10 días)
        Order.objects.filter(id=self.order.id).update(
            created_at=ten_days_ago, 
            final_amount=Decimal('20000.00')
        )

    def test_sales_velocity_success_math(self):
        """Prueba que el cálculo de velocidad y agotamiento sea matemáticamente exacto."""
        # Solicitamos periodo de 30 días, pero el sistema debe auto-ajustarse a 10 (por la primera venta)
        response = self.client.get(self.url, {'identifier': 'FAST123', 'period_days': 30})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data['product_name'], "Laptop Gamer")
        self.assertEqual(data['analyzed_period_days'], 10)  # El sistema detectó que solo lleva 10 días vendiéndose
        self.assertEqual(data['total_units_sold'], 20)
        self.assertEqual(data['sales_velocity'], 2.0)  # 20 unidades / 10 días
        self.assertEqual(data['depletion_estimation_days'], 50)  # 100 stock / 2.0 velocidad

    def test_sales_velocity_no_sales_indefinite(self):
        """Prueba un producto sin ventas. Validando el __iexact en la búsqueda."""
        # Lo buscamos en minúsculas para probar que el __iexact funciona
        response = self.client.get(self.url, {'identifier': 'mouse VIEJO'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data['total_units_sold'], 0)
        self.assertEqual(data['sales_velocity'], 0.0)
        self.assertEqual(data['depletion_estimation_days'], "Indefinida")

    def test_missing_identifier(self):
        """Prueba que tire error 400 si no se envía el parámetro obligatorio."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Product identifier (Name or SKU) is required.")

    def test_product_not_found(self):
        """Prueba que tire error 404 si el SKU o Nombre no existen."""
        response = self.client.get(self.url, {'identifier': 'FANTASMA999'})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Product not found in the system.")

class InventoryValuationTests(APITestCase):
    
    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@test.com', 'password')
        self.client.force_authenticate(user=self.user)

        self.supplier = Supplier.objects.create(
            name="Proveedor General", phone_number="123456789", rfc="ABC123456T1"
        )
        # Producto 1: Costo (price) 10.00
        # Al guardar -> final_price = 11.60 (10 + 16% IVA)
        # Stock: 5
        # Inversión: 50.00 | Venta Potencial: 58.00 | Ganancia: 8.00
        self.product_a = Product.objects.create(
            name="Teclado Mecánico",
            sku="TEC001",
            price=Decimal('10.00'), 
            current_stock=5,
            supplier_id = self.supplier.id,
        )
        # Producto 2: Costo (price) 50.00
        # Al guardar -> final_price = 58.00 (50 + 16% IVA)
        # Stock: 2 
        # Inversión: 100.00 | Venta Potencial: 116.00 | Ganancia: 16.00
        self.product_b = Product.objects.create(
            name="Monitor Gamer",
            sku="MON002",
            price=Decimal('50.00'),
            current_stock=2,
            supplier_id = self.supplier.id,
        )
        
        # Producto 3: Sin stock (Debería ser ignorado por el sistema)
        self.product_empty = Product.objects.create(
            name="Mouse Agotado",
            sku="MOU003",
            price=Decimal('5.00'),
            current_stock=0,
            supplier_id = self.supplier.id,
        )
        
        # Ajusta esta URL a la ruta de tu API
        self.url = '/api/analytics/inventory-valuation/' 

    def test_entire_inventory_valuation(self):
        """
        Prueba la valuación de todo el inventario con stock.
        Costo Total Esperado: 50.00 + 100.00 = 150.00
        Venta Total Esperada: 58.00 + 116.00 = 174.00
        Ganancia Esperada: 24.00
        Margen Esperado: (24.00 / 174.00) * 100 = 13.79%
        """
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        metrics = response.data['financial_metrics']
        
        self.assertEqual(response.data['scope'], "Entire Inventory")
        # Casteamos o comparamos flotantes dependiendo de cómo lo devuelva tu API
        self.assertEqual(metrics['total_inventory_cost'], Decimal('150.00'))
        self.assertEqual(metrics['total_potential_sale'], Decimal('174.00'))
        self.assertEqual(metrics['total_potential_profit'], Decimal('24.00'))
        self.assertEqual(metrics['profit_margin_percentage'], Decimal('13.79')) # 13.7931... redondeado a 2 decimales

    def test_specific_product_valuation(self):
        """Prueba la valuación de un producto específico buscado por SKU"""
        response = self.client.get(f"{self.url}?product_identifier=TEC001")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        metrics = response.data['financial_metrics']
        
        self.assertEqual(metrics['total_inventory_cost'], Decimal('50.00'))
        self.assertEqual(metrics['total_potential_sale'], Decimal('58.00'))
        self.assertEqual(metrics['total_potential_profit'], Decimal('8.00'))
        self.assertEqual(metrics['profit_margin_percentage'], Decimal('13.79'))

    def test_product_not_found_or_no_stock(self):
        """Prueba buscando un producto que no existe o que tiene stock en 0"""
        # Caso 1: Producto con stock en 0
        response_empty = self.client.get(f"{self.url}?product_identifier=MOU003")
        self.assertEqual(response_empty.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response_empty.data['error'], "No products available in the selected scope.")
        
        # Caso 2: Producto que no existe
        response_not_found = self.client.get(f"{self.url}?product_identifier=FANTASMA")
        self.assertEqual(response_not_found.status_code, status.HTTP_404_NOT_FOUND)
