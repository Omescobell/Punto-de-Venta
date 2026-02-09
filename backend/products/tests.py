from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone 
from datetime import date, timedelta   
from decimal import Decimal

from suppliers.models import Supplier
from .models import Product, Promotion

User = get_user_model()

class BaseTestCase(APITestCase):
    def setUp(self):
        # Configuración del Cliente
        self.client = APIClient()
        self.today = timezone.now().date()
        
        # 1. Usuarios (Admin y Empleado)
        self.admin_user = User.objects.create_superuser(
            username='admin_master',   
            email='admin@test.com', 
            password='password123',
            first_name='Admin',
            role='ADMIN'
        )
        
        self.employee_user = User.objects.create_user(
            username='vendedor_test',  # 
            email='employee@test.com', 
            password='password123',
            first_name='Vendedor',
            role='EMPLOYEE'
        )

        # 2. Proveedor General
        self.supplier = Supplier.objects.create(
            name="Proveedor General",
            phone_number="5555555555",      
            contact_person="Juan Pérez",    
            rfc="XAXX010101000",            
            tax_address="Av. Siempre Viva 123"
        )

        # 3. Producto Base (Para uso general)
        # Se crea con Stock 50 y Tax 16% (General)
        self.product = Product.objects.create(
            name="Producto Base",
            sku="BASE-001",
            price=Decimal('100.00'),
            current_stock=50,
            reserved_quantity=0,
            supplier=self.supplier,
            tax_rate="16.00" 
        )
        
        self.client.force_authenticate(user=self.admin_user)



class ProductAndPromotionTests(BaseTestCase):

    def setUp(self):
        super().setUp()


        self.products_list_url = reverse('product-list')
        self.promotions_list_url = reverse('promotion-list')


        self.tomorrow = self.today + timedelta(days=1)
        self.next_month = self.today + timedelta(days=30)

    #! TESTS DE PRODUCTOS

    def test_employee_can_create_product_with_tax(self):
        self.client.force_authenticate(user=self.employee_user)
        
        data = {
            "name": "Nuevo Producto",
            "sku": "SKU-002",
            "price": "50.00",
            "tax_rate": "16.00",
            "current_stock": 20,
            "supplier": self.supplier.id 
        }
        
        response = self.client.post(self.products_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2) # Base + Nuevo
        self.assertEqual(response.data['final_price'], "58.00")

    def test_tax_calculations_logic(self):
        p_frontier = Product.objects.create(
            name="Prod Frontera", sku="FRONT-1", price=Decimal("100.00"),
            tax_rate=Product.TaxType.FRONTIER, supplier=self.supplier
        )
        self.assertEqual(p_frontier.final_price, Decimal("108.00"))
        p_general = Product.objects.create(
            name="Prod General", sku="GENERAL-1", price=Decimal("100.00"),
            tax_rate=Product.TaxType.GENERAL, supplier=self.supplier
        )
        self.assertEqual(p_general.final_price, Decimal("116.00"))

        p_zero = Product.objects.create(
            name="Prod Cero", sku="ZERO-1", price=Decimal("100.00"),
            tax_rate=Product.TaxType.ZERO, supplier=self.supplier
        )
        self.assertEqual(p_zero.final_price, Decimal("100.00"))

        p_exempt = Product.objects.create(
            name="Prod Exento", sku="EXEMPT-1", price=Decimal("100.00"),
            tax_rate=Product.TaxType.EXEMPT, supplier=self.supplier
        )
        self.assertEqual(p_exempt.final_price, Decimal("100.00"))

    def test_final_price_is_readonly(self):
        self.client.force_authenticate(user=self.employee_user)
        data = {
            "name": "Intento Hack Precio",
            "sku": "HACK-001",
            "price": "100.00",
            "tax_rate": "16.00",
            "final_price": "10.00", # Este valor debe ser ignorado
            "supplier": self.supplier.id
        }
        response = self.client.post(self.products_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_product = Product.objects.get(sku="HACK-001")
        # El sistema debió calcular 116, ignorando el 10 enviado
        self.assertEqual(new_product.final_price, Decimal("116.00"))

    def test_employee_can_update_product_price_recalculates_tax(self):
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        data = {"price": 200.00}
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal("200.00"))
        self.assertEqual(self.product.final_price, Decimal("232.00"))

    def test_employee_cannot_delete_product(self):
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Product.objects.filter(id=self.product.id).exists())

    def test_admin_can_delete_product(self):
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    #! TESTS DE PROMOCIONES 

    def test_employee_can_see_promotions(self):
        self.client.force_authenticate(user=self.employee_user)
        
        Promotion.objects.create(
            name="Promo Existente",
            product=self.product,
            discount_percent=10,
            start_date=self.today,       
            end_date=self.next_month,    
            target_audience="ALL",
            is_active=True
        )

        response = self.client.get(self.promotions_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_employee_cannot_manage_promotions(self):
        self.client.force_authenticate(user=self.employee_user)
        
        data = {
            "name": "Intento Hack",
            "description": "Descuento",
            "product": self.product.id,
            "discount_percent": 50,
            "start_date": str(self.today),       
            "end_date": str(self.next_month),
            "target_audience": "ALL"
        }
        response = self.client.post(self.promotions_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Intentar borrar
        promo = Promotion.objects.create(
            name="Promo Test", 
            product=self.product, 
            discount_percent=10, 
            start_date=self.today,     
            end_date=self.next_month,  
            target_audience="ALL",
            is_active=True
        )
        url = reverse('promotion-detail', kwargs={'pk': promo.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_promotion(self):
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            "name": "Oferta Verano",
            "description": "Descuento válido",
            "product": self.product.id,
            "discount_percent": 20.00,
            "start_date": str(self.today),
            "end_date": str(self.next_month),
            "target_audience": "ALL"
        }
        
        response = self.client.post(self.promotions_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Promotion.objects.count(), 1)

    def test_promotion_date_validation(self):
        self.client.force_authenticate(user=self.admin_user)
        
        # Fechas ilógicas: Inicio posterior a Fin
        start = self.today + timedelta(days=10)
        end = self.today 

        data = {
            "name": "Oferta Erronea",
            "description": "Descripción obligatoria",
            "product": self.product.id,
            "discount_percent": 10,
            "start_date": str(start), 
            "end_date": str(end),   
            "target_audience": "ALL"
        }
        
        response = self.client.post(self.promotions_list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_message_part = "posterior a la fecha de inicio"
        self.assertIn(error_message_part, str(response.data))

    def test_admin_can_update_promotion_patch(self):
        self.client.force_authenticate(user=self.admin_user)
        
        promo = Promotion.objects.create(
            name="Promo Vieja",
            product=self.product,
            discount_percent=10,
            start_date=self.today,
            end_date=self.next_month,  
            target_audience="ALL",
            is_active=True
        )
        
        url = reverse('promotion-detail', kwargs={'pk': promo.id})
        data = {"name": "Promo Renovada"}
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        promo.refresh_from_db()
        self.assertEqual(promo.name, "Promo Renovada")

    def test_filter_promotions_by_product(self):
        self.client.force_authenticate(user=self.admin_user)
        
        # Creamos un segundo producto solo para este test
        product_2 = Product.objects.create(
            name="Otro Producto", sku="SKU-003", price=10, supplier=self.supplier
        )
        
        Promotion.objects.create(
            name="Promo P1", product=self.product, discount_percent=10, 
            start_date=self.today, end_date=self.tomorrow, 
            target_audience="ALL", is_active=True
        )
        Promotion.objects.create(
            name="Promo P2", product=product_2, discount_percent=10, 
            start_date=self.today, end_date=self.tomorrow, 
            target_audience="ALL", is_active=True
        )
        
        response = self.client.get(f"{self.promotions_list_url}?product={self.product.id}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Promo P1")
    
    def test_employee_can_reserve_stock(self):
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('product-manage-reservation', kwargs={'pk': self.product.id})
        
        # Reservar 5
        response = self.client.post(url, {"amount": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product.current_stock = 10
        self.product.reserved_quantity = 5 
        self.product.save()

        # Ahora intentar reservar 10 más (Total necesario 15 > Stock 10) -> Debe fallar
        response = self.client.post(url, {"amount": 10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Liberar 2
        response = self.client.post(url, {"amount": -2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_quantity, 3) # 5 - 2 = 3


class ProductStockTests(BaseTestCase):

    def test_reduce_stock_with_reservation_success(self):
        """Venta normal desde carrito (consume_reservation=True)."""
        self.product.current_stock = 50
        self.product.reserved_quantity = 10
        self.product.save()

        self.product.reduce_stock(5, consume_reservation=True)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 45)
        self.assertEqual(self.product.reserved_quantity, 5)

    def test_reduce_stock_direct_sale_preserves_reservation(self):
        """Venta directa fuera de carrito (consume_reservation=False)."""
        self.product.current_stock = 50
        self.product.reserved_quantity = 10
        self.product.save()

        self.product.reduce_stock(5, consume_reservation=False)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 45)
        self.assertEqual(self.product.reserved_quantity, 10) # Intacta

    def test_error_insufficient_physical_stock(self):
        """Intentar vender más de lo que existe físicamente."""
        self.product.current_stock = 5
        self.product.save()

        with self.assertRaises(ValidationError) as cm:
            self.product.reduce_stock(10)
        
        self.assertIn("Stock insuficiente", str(cm.exception))

    def test_error_insufficient_reserved_stock(self):
        """Intentar confirmar una venta reservada inexistente."""
        self.product.current_stock = 50
        self.product.reserved_quantity = 2  
        self.product.save()

        with self.assertRaises(ValidationError) as cm:
            self.product.reduce_stock(5, consume_reservation=True)
            
        self.assertIn("No hay suficiente stock reservado", str(cm.exception))


class CronJobTests(BaseTestCase):
    
    def setUp(self):
        super().setUp()

        self.cron_product = Product.objects.create(
            name="P Dormido", sku="ZZZ", price=100, supplier=self.supplier
        )

    def test_cron_activates_sleeping_promotion(self):
        """El script debe despertar promociones que inician hoy."""
        Promotion.objects.create(
            name="Despiertame",
            product=self.cron_product,
            discount_percent=50,
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            is_active=True
        )

        # Forzamos estado desincronizado
        self.cron_product.discounted_price = None 
        self.cron_product.save()

        count = Promotion.check_and_activate_promotions()

        self.cron_product.refresh_from_db()
        self.assertEqual(count, 1)
        self.assertEqual(self.cron_product.discounted_price, Decimal("50.00"))

    def test_cron_ignores_expired_or_future(self):
        """El script ignora promociones futuras."""
        Promotion.objects.create(
            name="Futura", product=self.cron_product, discount_percent=20,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=5),
            is_active=True
        )
        
        count = Promotion.check_and_activate_promotions()
        
        self.cron_product.refresh_from_db()
        self.assertEqual(count, 0)
        self.assertIsNone(self.cron_product.discounted_price)