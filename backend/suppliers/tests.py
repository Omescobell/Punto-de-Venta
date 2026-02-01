from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Supplier

# Obtenemos el modelo de usuario activo
User = get_user_model()

class SupplierTests(APITestCase):

    def setUp(self):
        """
        Configuración inicial que se ejecuta antes de CADA test.
        Creamos 3 usuarios con roles distintos.
        """
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='pass',
            role='ADMIN'   
        )

        self.owner_user = User.objects.create_user(
            username='owner_test',
            email='owner@test.com',
            password='pass',
            role='OWNER'   
        )

        self.employee_user = User.objects.create_user(
            username='employee_test',
            email='employee@test.com',
            password='pass',
            role='EMPLOYEE' 
        )

        self.url = reverse('supplier-list')

        # Datos de prueba para crear un proveedor
        self.supplier_data = {
            "name": "Proveedor de Prueba S.A.",
            "phone_number": "5512345678",
            "contact_person": "Lic. Valeriano",
            "rfc": "XAXX010101000",
            "tax_address": "Calle de las Pruebas 123"
        }

    #TEST 1: El Admin DEBE poder crear
    def test_admin_can_create_supplier(self):
        # Autenticamos como Admin
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.url, self.supplier_data)

        # Verificamos que se creó (201 Created)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificamos que se guardó en la base de datos
        self.assertEqual(Supplier.objects.count(), 1)
        self.assertEqual(Supplier.objects.get().name, "Proveedor de Prueba S.A.")

    #TEST 2: El Owner DEBE poder crear
    def test_owner_can_create_supplier(self):
        # Autenticamos como Owner
        self.client.force_authenticate(user=self.owner_user)

        response = self.client.post(self.url, self.supplier_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Supplier.objects.count(), 1)

    #TEST 3: El Empleado NO debe poder crear (Forbidden)
    def test_employee_cannot_create_supplier(self):
        # Autenticamos como Empleado
        self.client.force_authenticate(user=self.employee_user)

        response = self.client.post(self.url, self.supplier_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Aseguramos que NO se guardó nada en la BD
        self.assertEqual(Supplier.objects.count(), 0)

    #TEST 4: Usuario anónimo NO debe poder entrar
    def test_anonymous_cannot_access(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    #TEST 5: Verificar integridad de los datos
    def test_create_supplier_data_integrity(self):
        self.client.force_authenticate(user=self.admin_user)
        self.client.post(self.url, self.supplier_data)

        supplier = Supplier.objects.first()
        
        # Verificamos campo por campo
        self.assertEqual(supplier.phone_number, "5512345678")
        self.assertEqual(supplier.tax_address, "Calle de las Pruebas 123")
