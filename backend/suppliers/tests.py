from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Supplier

User = get_user_model()

class BaseSupplierTestCase(APITestCase):
    def setUp(self):
        """Configuración inicial compartida para todas las suites de pruebas."""
        self.admin_user = User.objects.create_user(
            username='admin_test', email='admin@test.com', password='pass', role='ADMIN'   
        )
        self.owner_user = User.objects.create_user(
            username='owner_test', email='owner@test.com', password='pass', role='OWNER'   
        )
        self.employee_user = User.objects.create_user(
            username='employee_test', email='employee@test.com', password='pass', role='EMPLOYEE' 
        )
        self.url = reverse('supplier-list')
        self.supplier_data = {
            "name": "Proveedor de Prueba S.A.",
            "phone_number": "5512345678",
            "contact_person": "Lic. Valeriano",
            "rfc": "XAXX010101000",
            "tax_address": "Calle de las Pruebas 123"
        }

class SupplierUnitTests(BaseSupplierTestCase):
    
    # Verifica RQNF55: Integridad de los datos en el payload
    def test_create_supplier_data_integrity(self):
        self.client.force_authenticate(user=self.admin_user)
        self.client.post(self.url, self.supplier_data)

        supplier = Supplier.objects.first()
        
        # Verificamos campo por campo la integridad de los datos guardados
        self.assertEqual(supplier.name, "Proveedor de Prueba S.A.")
        self.assertEqual(supplier.phone_number, "5512345678")
        self.assertEqual(supplier.contact_person, "Lic. Valeriano")
        self.assertEqual(supplier.rfc, "XAXX010101000")
        self.assertEqual(supplier.tax_address, "Calle de las Pruebas 123")


class SupplierIntegrationTests(BaseSupplierTestCase):

    # Verifica RQNF54: Relación Vista - Permisos (Empleado)
    def test_employee_cannot_create_supplier(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(self.url, self.supplier_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Supplier.objects.count(), 0)

    # Verifica RQNF54: Relación Vista - Permisos (Anónimo)
    def test_anonymous_cannot_access(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class SupplierFunctionalTests(BaseSupplierTestCase):

    # Verifica RQF34 y RQF35: Creación exitosa por Admin
    def test_admin_can_create_supplier(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.url, self.supplier_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Supplier.objects.count(), 1)

    # Verifica RQF34 y RQF35: Creación exitosa por Owner
    def test_owner_can_create_supplier(self):
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.post(self.url, self.supplier_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Supplier.objects.count(), 1)