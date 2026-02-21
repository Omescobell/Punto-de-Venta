from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone   
from decimal import Decimal
from datetime import timedelta
from django.core.management import call_command

from suppliers.models import Supplier
from .models import Product, Promotion
from orders.models import Order, OrderItems

User = get_user_model()


class BaseProductTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.today = timezone.now().date()
        self.tomorrow = self.today + timedelta(days=1)
        self.next_month = self.today + timedelta(days=30)
        
        self.admin_user = User.objects.create_superuser(
            username='admin_master', email='admin@test.com', password='password123', role='ADMIN'
        )
        self.employee_user = User.objects.create_user(
            username='vendedor_test', email='employee@test.com', password='password123', role='EMPLOYEE'
        )

        self.supplier = Supplier.objects.create(
            name="Proveedor General", phone_number="5555555555", contact_person="Juan Pérez", 
            rfc="XAXX010101000", tax_address="Av. Siempre Viva 123"
        )

        self.product = Product.objects.create(
            name="Producto Base", sku="BASE-001", price=Decimal('100.00'), current_stock=50, 
            reserved_quantity=0, supplier=self.supplier, tax_rate="16.00" 
        )

        self.products_list_url = reverse('product-list')
        self.promotions_list_url = reverse('promotion-list')

        # Mock para pruebas de clientes
        class MockCustomer:
            def __init__(self, is_frequent):
                self.is_frequent = is_frequent
        self.vip_customer = MockCustomer(is_frequent=True)
        self.regular_customer = MockCustomer(is_frequent=False)


class ProductUnitTests(BaseProductTestCase):

    def test_tax_calculations_logic(self):
        p_frontier = Product.objects.create(name="Prod Frontera", sku="FRONT-1", price=Decimal("100.00"), tax_rate=Product.TaxType.FRONTIER, supplier=self.supplier)
        self.assertEqual(p_frontier.final_price, Decimal("108.00"))
        
        p_general = Product.objects.create(name="Prod General", sku="GENERAL-1", price=Decimal("100.00"), tax_rate=Product.TaxType.GENERAL, supplier=self.supplier)
        self.assertEqual(p_general.final_price, Decimal("116.00"))

        p_zero = Product.objects.create(name="Prod Cero", sku="ZERO-1", price=Decimal("100.00"), tax_rate=Product.TaxType.ZERO, supplier=self.supplier)
        self.assertEqual(p_zero.final_price, Decimal("100.00"))

        p_exempt = Product.objects.create(name="Prod Exento", sku="EXEMPT-1", price=Decimal("100.00"), tax_rate=Product.TaxType.EXEMPT, supplier=self.supplier)
        self.assertEqual(p_exempt.final_price, Decimal("100.00"))

    def test_reduce_stock_with_reservation_success(self):
        self.product.reserved_quantity = 10
        self.product.save()
        self.product.reduce_stock(5, consume_reservation=True)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 45)
        self.assertEqual(self.product.reserved_quantity, 5)

    def test_reduce_stock_direct_sale_preserves_reservation(self):
        self.product.reserved_quantity = 10
        self.product.save()
        self.product.reduce_stock(5, consume_reservation=False)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 45)
        self.assertEqual(self.product.reserved_quantity, 10)

    def test_error_insufficient_physical_stock(self):
        self.product.current_stock = 5
        self.product.save()
        with self.assertRaises(ValidationError) as cm:
            self.product.reduce_stock(10)
        self.assertIn("Stock insuficiente", str(cm.exception))

    def test_error_insufficient_reserved_stock(self):
        self.product.reserved_quantity = 2  
        self.product.save()
        with self.assertRaises(ValidationError) as cm:
            self.product.reduce_stock(5, consume_reservation=True)
        self.assertIn("No hay suficiente stock reservado", str(cm.exception))

    def test_promotion_vip_applies_only_to_frequent_customer(self):
        Promotion.objects.create(
            name="Promo VIP Exclusiva", product=self.product, discount_percent=10, 
            start_date=self.today, end_date=self.tomorrow, target_audience="FREQUENT_ONLY", is_active=True
        )
        self.product.refresh_from_db()

        base_normal, final_normal, name_normal = self.product.get_dynamic_price(self.regular_customer)
        self.assertEqual(final_normal, Decimal("116.00"))

        base_vip, final_vip, name_vip = self.product.get_dynamic_price(self.vip_customer)
        self.assertEqual(final_vip, Decimal("104.40"))
        self.assertEqual(name_vip, "Promo VIP Exclusiva")

    def test_promotion_general_applies_to_everyone(self):
        Promotion.objects.create(
            name="Promo General Verano", product=self.product, discount_percent=20, 
            start_date=self.today, end_date=self.tomorrow, target_audience="ALL", is_active=True
        )
        self.product.refresh_from_db()

        _, final_n, name_n = self.product.get_dynamic_price(self.regular_customer)
        self.assertEqual(final_n, Decimal("92.80"))
        self.assertEqual(name_n, "Promo General Verano")

        _, final_v, _ = self.product.get_dynamic_price(self.vip_customer)
        self.assertEqual(final_v, Decimal("92.80"))

    def test_dynamic_price_without_customer_instance(self):
        Promotion.objects.create(
            name="Promo VIP Oculta", product=self.product, discount_percent=50, 
            start_date=self.today, end_date=self.tomorrow, target_audience="FREQUENT_ONLY", is_active=True
        )
        self.product.refresh_from_db()
        base, final, name = self.product.get_dynamic_price(None)
        self.assertEqual(final, Decimal("116.00"))
        self.assertIsNone(name)


class ProductIntegrationTests(BaseProductTestCase):

    def test_final_price_is_readonly(self):
        self.client.force_authenticate(user=self.employee_user)
        data = {"name": "Hack", "sku": "HACK-001", "price": "100.00", "tax_rate": "16.00", "final_price": "10.00", "supplier": self.supplier.id}
        self.client.post(self.products_list_url, data)
        new_product = Product.objects.get(sku="HACK-001")
        self.assertEqual(new_product.final_price, Decimal("116.00"))

    def test_employee_cannot_delete_product(self):
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_manage_promotions(self):
        self.client.force_authenticate(user=self.employee_user)
        data = {"name": "Intento Hack", "product": self.product.id, "discount_percent": 50, "start_date": str(self.today), "end_date": str(self.next_month), "target_audience": "ALL"}
        response = self.client.post(self.promotions_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        promo = Promotion.objects.create(name="Promo Test", product=self.product, discount_percent=10, start_date=self.today, end_date=self.next_month, target_audience="ALL", is_active=True)
        response_del = self.client.delete(reverse('promotion-detail', kwargs={'pk': promo.id}))
        self.assertEqual(response_del.status_code, status.HTTP_403_FORBIDDEN)

    def test_promotion_date_validation(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "Error", "description": "Desc", "product": self.product.id, "discount_percent": 10, "start_date": str(self.today + timedelta(days=10)), "end_date": str(self.today), "target_audience": "ALL"}
        response = self.client.post(self.promotions_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class ProductFunctionalTests(BaseProductTestCase):

    def test_employee_can_create_product_with_tax(self):
        self.client.force_authenticate(user=self.employee_user)
        data = {"name": "Nuevo Producto", "sku": "SKU-002", "price": "50.00", "tax_rate": "16.00", "current_stock": 20, "supplier": self.supplier.id}
        response = self.client.post(self.products_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['final_price'], "58.00")

    def test_employee_can_update_product_price_recalculates_tax(self):
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        response = self.client.patch(url, {"price": 200.00})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.final_price, Decimal("232.00"))

    def test_admin_can_delete_product(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_employee_can_see_promotions(self):
        self.client.force_authenticate(user=self.employee_user)
        Promotion.objects.create(name="Promo Existente", product=self.product, discount_percent=10, start_date=self.today, end_date=self.next_month, target_audience="ALL", is_active=True)
        response = self.client.get(self.promotions_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_admin_can_create_promotion(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "Oferta Verano", "description": "Desc", "product": self.product.id, "discount_percent": 20.00, "start_date": str(self.today), "end_date": str(self.next_month), "target_audience": "ALL"}
        response = self.client.post(self.promotions_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_update_promotion_patch(self):
        self.client.force_authenticate(user=self.admin_user)
        promo = Promotion.objects.create(name="Promo Vieja", product=self.product, discount_percent=10, start_date=self.today, end_date=self.next_month, target_audience="ALL", is_active=True)
        url = reverse('promotion-detail', kwargs={'pk': promo.id})
        response = self.client.patch(url, {"name": "Promo Renovada"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        promo.refresh_from_db()
        self.assertEqual(promo.name, "Promo Renovada")

    def test_filter_promotions_by_product(self):
        self.client.force_authenticate(user=self.admin_user)
        product_2 = Product.objects.create(name="Otro", sku="S-3", price=10, supplier=self.supplier)
        Promotion.objects.create(name="Promo P1", product=self.product, discount_percent=10, start_date=self.today, end_date=self.tomorrow, target_audience="ALL", is_active=True)
        Promotion.objects.create(name="Promo P2", product=product_2, discount_percent=10, start_date=self.today, end_date=self.tomorrow, target_audience="ALL", is_active=True)
        
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

        # Fallar al exceder
        response = self.client.post(url, {"amount": 10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Liberar 2
        response = self.client.post(url, {"amount": -2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_quantity, 3) 

class ProductSystemAndCronTests(BaseProductTestCase):

    def test_cron_activates_sleeping_promotion(self):
        Promotion.objects.create(name="Despiertame", product=self.product, discount_percent=50, start_date=self.today, end_date=self.today + timedelta(days=5), is_active=True)
        self.product.discounted_price = None 
        self.product.save()

        count = Promotion.check_and_activate_promotions()
        self.product.refresh_from_db()
        self.assertEqual(count, 1)
        self.assertEqual(self.product.discounted_price, Decimal("50.00"))

    def test_cron_ignores_expired_or_future(self):
        Promotion.objects.create(name="Futura", product=self.product, discount_percent=20, start_date=self.tomorrow, end_date=self.today + timedelta(days=5), is_active=True)
        count = Promotion.check_and_activate_promotions()
        self.product.refresh_from_db()
        self.assertEqual(count, 0)
        self.assertIsNone(self.product.discounted_price)

    def test_low_stock_se_activa_via_comando(self):
        first_this_month = timezone.localtime(timezone.now()).replace(day=1)
        fecha_mes_pasado = first_this_month - timedelta(days=15)

        order = Order.objects.create(status='PAID', subtotal=1500, final_amount=1500)
        order.created_at = fecha_mes_pasado
        order.save()

        OrderItems.objects.create(order=order, product=self.product, quantity=100, product_name=self.product.name, unit_price=self.product.price, amount=1500)

        call_command('update_low_stock')

        self.product.refresh_from_db()
        self.assertTrue(self.product.low_stock)