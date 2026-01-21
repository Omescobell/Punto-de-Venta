from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Customer

User = get_user_model()

class CustomerTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='cajero',
            email='cajero@test.com',
            password='password123',
            role='EMPLOYEE'
        )
        
        self.url = reverse('customer-list')

        self.valid_payload = {
            "first_name": "Juan",
            "last_name": "Pérez",
            "phone_number": "5512345678",
            "email": "juan@cliente.com",
            "birth_date": "1990-05-15"
        }

    def test_create_customer_success(self):
        """Prueba que un usuario autenticado puede crear un cliente."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.valid_payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(Customer.objects.get().first_name, "Juan")

    def test_is_frequent_is_readonly(self):
        """
        Prueba que 'is_frequent' no se puede activar manualmente al crear.
        Debe permanecer en False por defecto.
        """
        self.client.force_authenticate(user=self.user)
        
        payload = self.valid_payload.copy()
        payload['is_frequent'] = True
        
        response = self.client.post(self.url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verificamos en BD que ignoró el True y puso False
        self.assertFalse(Customer.objects.get().is_frequent)

    def test_duplicate_email_fails(self):
        """Prueba que no se pueden crear dos clientes con el mismo email."""
        self.client.force_authenticate(user=self.user)
        
        # Creamos el primero
        self.client.post(self.url, self.valid_payload)
        
        # Intentamos crear el segundo con mismos datos
        response = self.client.post(self.url, self.valid_payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data) # El error debe estar en el campo email

    def test_duplicate_phone_fails(self):
        """Prueba que no se pueden crear dos clientes con el mismo teléfono."""
        self.client.force_authenticate(user=self.user)
        
        # Creamos el primero
        self.client.post(self.url, self.valid_payload)
        
        # Intentamos crear otro con diferente email pero mismo teléfono
        payload_2 = self.valid_payload.copy()
        payload_2['email'] = 'otro@mail.com' # Email diferente para que no falle por eso
        
        response = self.client.post(self.url, payload_2)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)

    def test_missing_required_fields(self):
        """Prueba que fallará si faltan campos obligatorios."""
        self.client.force_authenticate(user=self.user)
        
        # Payload vacío
        response = self.client.post(self.url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)
        self.assertIn('phone_number', response.data)