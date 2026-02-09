from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone 
from datetime import timedelta   
from suppliers.models import Supplier
from .models import Product, Promotion
from decimal import Decimal

User = get_user_model()

class ProductAndPromotionTests(APITestCase):

    def setUp(self):
        # 1. Usuarios con Roles
        self.admin_user = User.objects.create_user(
            username='admin_test', email='admin@test.com', password='pass', role='ADMIN'
        )
        self.employee_user = User.objects.create_user(
            username='employee_test', email='emp@test.com', password='pass', role='EMPLOYEE'
        )

        # 2. Proveedor
        self.supplier = Supplier.objects.create(
            name="Proveedor Test",
            phone_number="5555555555",
            rfc="RFC123",
            tax_address="Calle Test"
        )

        # 3. Producto Base
        self.product = Product.objects.create(
            name="Producto Base",
            sku="SKU-001",
            price=Decimal('100.00'),
            tax_rate=Product.TaxType.GENERAL, 
            current_stock=10,
            supplier=self.supplier
        )
        # Forzamos el guardado para asegurar que se ejecute el cálculo de final_price
        self.product.save()


        self.products_list_url = reverse('product-list')
        self.promotions_list_url = reverse('promotion-list')


        self.today = timezone.now().date()
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
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(response.data['final_price'], "58.00")

    def test_tax_calculations_logic(self):
        p_frontier = Product.objects.create(
            name="Prod Frontera", sku="FRONT-1", price=Decimal("100.00"),
            tax_rate=Product.TaxType.FRONTIER, supplier=self.supplier
        )
        p_general = Product.objects.create(
            name="Prod General", sku="GENERAL-1", price=Decimal("100.00"),
            tax_rate=Product.TaxType.GENERAL, supplier=self.supplier
        )
        self.assertEqual(p_frontier.final_price, Decimal("108.00"))

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
            "final_price": "10.00",
            "supplier": self.supplier.id
        }
        response = self.client.post(self.products_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_product = Product.objects.get(sku="HACK-001")
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
        self.client.force_authenticate(user=self.admin_user)
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
        """El Admin crea una promoción correctamente vía API."""
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
        """Validación: Inicio > Fin."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Fechas ilógicas: Inicio (hoy + 10 días) > Fin (hoy)
        start = self.today + timedelta(days=10)
        end = self.today 

        data = {
            "name": "Oferta Erronea",
            "description": "Descripción obligatoria para pasar validación",
            "product": self.product.id,
            "discount_percent": 10,
            "start_date": str(start), 
            "end_date": str(end),   
            "target_audience": "ALL"
        }
        
        response = self.client.post(self.promotions_list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_message_part = "posterior a la fecha de inicio"
        
        self.assertIn(
            error_message_part, 
            str(response.data),
            f"El mensaje de error esperado ('{error_message_part}') no se encontró en la respuesta."
        )

    def test_admin_can_update_promotion_patch(self):
        self.client.force_authenticate(user=self.admin_user)
        
        promo = Promotion.objects.create(
            name="Promo Vieja",
            product=self.product,
            discount_percent=10,
            start_date=self.today,     #
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
        
        response = self.client.post(url, {"amount": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.post(url, {"amount": 10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(url, {"amount": -2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_quantity, 3)