from decimal import Decimal
from datetime import timedelta
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from products.models import Product, Promotion
from suppliers.models import Supplier # Asegúrate de que esta ruta sea correcta

User = get_user_model()

class BaseTestCase(APITestCase):
    def setUp(self):
        # 1. Usuarios
        self.admin = User.objects.create_user(username='admin', password='password', role='ADMIN')
        self.employee = User.objects.create_user(username='employee', password='password', role='EMPLOYEE')
        
        # 2. Proveedor
        self.supplier = Supplier.objects.create(name="Prov Test", rfc="RFC123", phone_number="555")

        # 3. URLs
        self.product_url = reverse('product-list') 
        self.promotion_url = reverse('promotion-list')


class ProductTaxTests(BaseTestCase):
    
    def test_calculate_tax_general_16(self):
        """Valida: Precio 100 + 16% IVA = 116.00"""
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "Prod 16", "sku": "SKU-16", "price": "100.00",
            "tax_rate": "16.00", "supplier": self.supplier.id
        }
        res = self.client.post(self.product_url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(res.data['final_price']), Decimal("116.00"))

    def test_calculate_tax_frontier_8(self):
        """Valida: Precio 100 + 8% IVA = 108.00 (Frontera)"""
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "Prod 8", "sku": "SKU-08", "price": "100.00",
            "tax_rate": "8.00", "supplier": self.supplier.id
        }
        res = self.client.post(self.product_url, data)
        self.assertEqual(Decimal(res.data['final_price']), Decimal("108.00"))

    def test_sku_normalization(self):
        """Valida: '  sku-abc  ' se guarda como 'SKU-ABC'"""
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "Prod SKU", "sku": "  sku-lower  ", "price": "100", 
            "supplier": self.supplier.id
        }
        self.client.post(self.product_url, data)
        product = Product.objects.get(name="Prod SKU")
        self.assertEqual(product.sku, "SKU-LOWER")

class PromotionOverlapTests(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin)
        # Producto Base
        self.product = Product.objects.create(
            name="P1", sku="P1", price=100, supplier=self.supplier
        )
        
        # FECHAS BASE: Del 10 al 20 del mes actual
        self.today = timezone.now().date()
        self.base_start = self.today + timedelta(days=10)
        self.base_end = self.today + timedelta(days=20)
        
        # Crear Promoción Existente (La que "estorba")
        self.promo_existente = Promotion.objects.create(
            name="Promo Existente",
            product=self.product,
            discount_percent=10,
            start_date=self.base_start,
            end_date=self.base_end,
            is_active=True
        )

    def test_overlap_detection_logic_priority(self):
        """
        PRUEBA CRÍTICA:
        Intentamos crear una promo que choca (días 15 a 25).
        El sistema debe fallar PRIMERO por solapamiento y SUGERIR fechas.
        """
        # Intentamos: Inicio 15 (choca con 10-20), Fin 25
        new_start = self.base_start + timedelta(days=5) # Día 15
        new_end = self.base_end + timedelta(days=5)     # Día 25
        
        data = {
            "name": "Promo Chocante",
            "product": self.product.id,
            "discount_percent": 20,
            "start_date": new_start,
            "end_date": new_end,
            "target_audience": "ALL"
        }
        
        response = self.client.post(self.promotion_url, data)
        
        # 1. Debe fallar
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 2. Debe ser error de 'non_field_errors' (nuestra validación custom)
        errors = response.data.get('non_field_errors', [])
        self.assertTrue(len(errors) > 0)
        
        error_msg = str(errors[0])
        
        # 3. Validar las SUGERENCIAS matemáticas
        # La existente acaba el día 20. Sugerencia debe ser "después del 21".
        expected_suggest_after = str(self.base_end + timedelta(days=1))
        
        # La existente empieza el día 10. Sugerencia debe ser "antes del 9".
        expected_suggest_before = str(self.base_start - timedelta(days=1))
        
        print(f"\n[TEST LOG] Mensaje recibido: {error_msg}")
        
        self.assertIn("El rango choca", error_msg)
        self.assertIn(expected_suggest_before, error_msg, "Debería sugerir la fecha anterior")
        self.assertIn(expected_suggest_after, error_msg, "Debería sugerir la fecha posterior")

    def test_start_date_after_end_date_check(self):
        """
        Valida que si NO hay choque, entonces cheque start > end.
        """
        # Fechas lejanas sin choque (Día 50 al 40 -> Error Lógico)
        bad_start = self.today + timedelta(days=50)
        bad_end = self.today + timedelta(days=40)
        
        data = {
            "name": "Promo Error Logico",
            "product": self.product.id,
            "discount_percent": 20,
            "start_date": bad_start, # Mayor
            "end_date": bad_end,     # Menor
            "target_audience": "ALL"
        }
        
        response = self.client.post(self.promotion_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Aquí el error debe ser de campo 'end_date', no el mensaje complejo de sugerencias
        self.assertIn('end_date', response.data)

class PromotionApplicationTests(BaseTestCase):
    
    def setUp(self):
        super().setUp()
        self.product = Product.objects.create(
            name="P1", sku="P1", price=100, supplier=self.supplier
        )

    def test_active_promotion_applies_discount(self):
        """Si la fecha es hoy, el precio debe bajar."""
        today = timezone.now().date()
        
        Promotion.objects.create(
            name="Promo Hoy",
            product=self.product,
            discount_percent=50, # 100 -> 50
            start_date=today,
            end_date=today + timedelta(days=1),
            is_active=True
        )
        
        self.product.refresh_from_db()
        # Precio Base: 50. IVA 16% de 50 = 8. Final = 58.
        self.assertEqual(self.product.discounted_price, Decimal("50.00"))
        self.assertEqual(self.product.final_price, Decimal("58.00"))

    def test_future_promotion_does_not_apply_yet(self):
        """Si la fecha es futura, precio se mantiene normal."""
        future_start = timezone.now().date() + timedelta(days=5)
        
        Promotion.objects.create(
            name="Promo Futura",
            product=self.product,
            discount_percent=50,
            start_date=future_start,
            end_date=future_start + timedelta(days=5),
            is_active=True
        )
        
        self.product.refresh_from_db()
        self.assertIsNone(self.product.discounted_price)
        self.assertEqual(self.product.final_price, Decimal("116.00")) # 100 + 16%

class InventoryTests(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin)
        self.product = Product.objects.create(
            name="P Stock", sku="STOCK-1", price=100, current_stock=10, supplier=self.supplier
        )
        self.url = reverse('product-manage-reservation', kwargs={'pk': self.product.id})

    def test_reserve_success(self):
        """Reserva 3 items correctamente."""
        res = self.client.post(self.url, {"amount": 3})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_quantity, 3)
        # API debe devolver disponibles reales (10 - 3 = 7)
        self.assertEqual(res.data['available_to_sell'], 7)

    def test_reserve_insufficient_stock(self):
        """Intenta reservar 15 cuando hay 10."""
        res = self.client.post(self.url, {"amount": 15})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Stock insuficiente", str(res.data))

    def test_release_reservation(self):
        """Libera items (amount negativo)."""
        # Primero reservamos 5 manualmente
        self.product.reserved_quantity = 5
        self.product.save()

        # Liberamos 2
        res = self.client.post(self.url, {"amount": -2})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_quantity, 3) # 5 - 2 = 3

    def test_cannot_release_more_than_reserved(self):
        """Intenta liberar 10 cuando solo hay 5 reservados."""
        self.product.reserved_quantity = 5
        self.product.save()

        res = self.client.post(self.url, {"amount": -10})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class CronJobTests(BaseTestCase):
    """
    Prueba la función que correría antes de crear una orden.
    """
    def setUp(self):
        super().setUp()
        self.product = Product.objects.create(
            name="P Dormido", sku="ZZZ", price=100, supplier=self.supplier
        )
        self.today = timezone.now().date()

    def test_cron_activates_sleeping_promotion(self):
        """
        Escenario: 
        1. Existe una promo que empieza HOY.
        2. El producto AÚN NO tiene el precio actualizado (está 'dormido').
        3. Corremos el script y debe 'despertar' el precio.
        """
        # 1. Crear promo activa para hoy
        Promotion.objects.create(
            name="Despiertame",
            product=self.product,
            discount_percent=50,
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            is_active=True
        )

        # Verificamos que al crearse (sin pasar por serializer/view) el precio base sigue igual
        # Forzamos que esté 'mal' para probar que el script lo arregla
        self.product.discounted_price = None 
        self.product.save()

        # 2. EJECUTAR EL SCRIPT MAESTRO
        count = Promotion.check_and_activate_promotions()

        # 3. Validaciones
        self.product.refresh_from_db()
        
        print(f"\n[TEST CRON] Promociones activadas: {count}")
        
        self.assertEqual(count, 1, "Debería haber activado 1 promoción")
        self.assertEqual(self.product.discounted_price, Decimal("50.00"), "El precio debió actualizarse a 50")

    def test_cron_ignores_expired_or_future(self):
        """
        El script no debe tocar promociones vencidas o futuras.
        """
        # Promo Futura (Mañana)
        Promotion.objects.create(
            name="Futura", product=self.product, discount_percent=20,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=5),
            is_active=True
        )
        
        # Ejecutar script
        count = Promotion.check_and_activate_promotions()
        
        self.product.refresh_from_db()
        self.assertEqual(count, 0, "No debería activar nada futuro")
        self.assertIsNone(self.product.discounted_price, "El precio debe seguir intacto")