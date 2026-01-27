from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from suppliers.models import Supplier
from .models import Product, Promotion

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
            price=100.00,
            current_stock=10,
            supplier=self.supplier
        )

        # URLs
        self.products_list_url = reverse('product-list')
        self.promotions_list_url = reverse('promotion-list')

    #! TESTS DE PRODUCTOS

    def test_employee_can_create_product(self):
        """El empleado SÍ debe poder crear productos (operativo)."""
        self.client.force_authenticate(user=self.employee_user)
        
        data = {
            "name": "Nuevo Producto",
            "sku": "SKU-002",
            "price": 50.00,
            "current_stock": 20,
            "supplier": self.supplier.id
        }
        
        response = self.client.post(self.products_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)

    def test_employee_can_update_product(self):
        """El empleado SÍ debe poder editar productos (ej: cambiar stock)."""
        self.client.force_authenticate(user=self.employee_user)
        
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        data = {"price": 150.00}
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, 150.00)

    def test_employee_cannot_delete_product(self):
        """SEGURIDAD: El empleado NO puede borrar productos."""
        self.client.force_authenticate(user=self.employee_user)
        
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # El producto debe seguir existiendo
        self.assertTrue(Product.objects.filter(id=self.product.id).exists())

    def test_admin_can_delete_product(self):
        """El Admin SÍ puede borrar productos."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    #! TESTS DE PROMOCIONES

    def test_employee_can_see_promotions(self):
        """
        El empleado puede ver promociones
        """
        self.client.force_authenticate(user=self.employee_user)
        Promotion.objects.create(
            name="Promo Existente",
            product=self.product,
            discount_percent=10,
            start_date="2023-01-01",
            end_date="2023-01-31",
            target_audience="ALL"
        )

        response = self.client.get(self.promotions_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_employee_cannot_manage_promotions(self):
        """
        SEGURIDAD: Aunque puede verlas, el empleado NO puede crear, 
        editar ni borrar promociones.
        """
        self.client.force_authenticate(user=self.employee_user)
        
        data = {
            "name": "Intento Hack",
            "description": "Descuento válido por temporada",
            "product": self.product.id,
            "discount_percent": 50,
            "start_date": "2023-01-01",
            "end_date": "2023-01-02",
            "target_audience": "ALL"
        }
        response = self.client.post(self.promotions_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        promo = Promotion.objects.create(
            name="Promo Test", product=self.product, discount_percent=10, 
            start_date="2023-01-01", end_date="2023-01-31", target_audience="ALL"
        )
        url = reverse('promotion-detail', kwargs={'pk': promo.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_promotion(self):
        """El Admin crea una promoción correctamente."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            "name": "Oferta Verano",
            "description": "Descuento válido por temporada",
            "product": self.product.id,
            "discount_percent": 20.00,
            "start_date": "2023-06-01",
            "end_date": "2023-06-30",
            "target_audience": "ALL"
        }
        
        response = self.client.post(self.promotions_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Promotion.objects.count(), 1)
        self.assertEqual(Promotion.objects.first().product, self.product)

    def test_promotion_date_validation(self):
        """
        VALIDACIÓN: La fecha de inicio no puede ser mayor a la de fin.
        """
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            "name": "Oferta Erronea",
            "description": "Descripción de prueba",
            "product": self.product.id,
            "discount_percent": 10,
            "start_date": "2023-07-01", # Julio
            "end_date": "2023-06-01",   # Junio 
            "target_audience": "ALL"
        }
        
        response = self.client.post(self.promotions_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Verificamos que el error venga del validador que escribimos
        self.assertIn("La fecha de finalización debe ser posterior a la fecha de inicio.", str(response.data))

    def test_admin_can_update_promotion_patch(self):
        """Prueba de edición parcial (PATCH) de una promoción."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Creamos una promo previa
        promo = Promotion.objects.create(
            name="Promo Vieja",
            product=self.product,
            discount_percent=10,
            start_date="2023-01-01",
            end_date="2023-01-31",
            target_audience="ALL"
        )
        
        url = reverse('promotion-detail', kwargs={'pk': promo.id})
        
        data = {"name": "Promo Renovada"}
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        promo.refresh_from_db()
        self.assertEqual(promo.name, "Promo Renovada")
        # Aseguramos que las fechas (que no enviamos) sigan intactas
        self.assertEqual(str(promo.start_date), "2023-01-01")

    def test_filter_promotions_by_product(self):
        """
        Prueba que el filtro ?product=ID funciona.
        """
        self.client.force_authenticate(user=self.admin_user)
        
        product_2 = Product.objects.create(
            name="Otro Producto",
            sku="SKU-003",
            price=10,
            supplier=self.supplier
        )
        
        Promotion.objects.create(
            name="Promo P1", product=self.product, discount_percent=10, 
            start_date="2023-01-01", end_date="2023-01-02", target_audience="ALL"
        )
        Promotion.objects.create(
            name="Promo P2", product=product_2, discount_percent=10, 
            start_date="2023-01-01", end_date="2023-01-02", target_audience="ALL"
        )
        
        response = self.client.get(f"{self.promotions_list_url}?product={self.product.id}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Promo P1")
    
    def test_employee_can_reserve_stock(self):
        """Prueba la lógica de reserva y validación de stock."""
        self.client.force_authenticate(user=self.employee_user)
        
        url = reverse('product-manage-reservation', kwargs={'pk': self.product.id})
        
        # 1. Intento reservar 5 (Éxito)
        response = self.client.post(url, {"amount": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_quantity, 5)

        # 2. Intento reservar 10 más-> ERROR
        response = self.client.post(url, {"amount": 10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Insufficient stock", str(response.data))

        # 3. Intento liberar (restar) 2 -> Éxito (quedan 3)
        response = self.client.post(url, {"amount": -2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_quantity, 3)