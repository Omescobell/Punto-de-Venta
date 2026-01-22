from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Customer, PointsTransaction

User = get_user_model()

class CustomerTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='cajero',
            email='cajero@test.com',
            password='password123',
            role='EMPLOYEE'
        )

        self.customer = Customer.objects.create(
            first_name="Cliente",
            last_name="Base",
            phone_number="5500000000",
            email="base@cliente.com",
            birth_date="1990-01-01"
        )

        self.list_url = reverse('customer-list')

        self.valid_payload = {
            "first_name": "Juan",
            "last_name": "Pérez",
            "phone_number": "5512345678",
            "email": "juan@cliente.com",
            "birth_date": "1990-05-15"
        }



    def test_create_customer_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 2) 

    def test_is_frequent_is_readonly(self):
        self.client.force_authenticate(user=self.user)
        payload = self.valid_payload.copy()
        payload['is_frequent'] = True
        response = self.client.post(self.list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(Customer.objects.last().is_frequent)

    def test_duplicate_email_fails(self):
        self.client.force_authenticate(user=self.user)
        # Creamos uno
        self.client.post(self.list_url, self.valid_payload)
        # Intentamos repetir
        response = self.client.post(self.list_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_duplicate_phone_fails(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(self.list_url, self.valid_payload)
        payload_2 = self.valid_payload.copy()
        payload_2['email'] = 'otro@mail.com'
        response = self.client.post(self.list_url, payload_2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)

    def test_missing_required_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ! Tests sistema de puntos

    def test_earn_points_updates_balance_and_creates_transaction(self):
        self.client.force_authenticate(user=self.user)
        
        url = reverse('customer-points', kwargs={'pk': self.customer.id})
        
        data = {
            "amount": 100,
            "transaction_type": "EARN",
            "description": "Compra Test"
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_points, 100)
        self.assertEqual(PointsTransaction.objects.count(), 1)

    def test_redeem_points_decreases_balance(self):
        self.client.force_authenticate(user=self.user)
        
        self.customer.current_points = 500
        self.customer.save()
        
        url = reverse('customer-points', kwargs={'pk': self.customer.id})
        
        data = {
            "amount": -200,
            "transaction_type": "REDEEM",
            "description": "Canje"
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_points, 300)

    def test_points_history_endpoint(self):
        self.client.force_authenticate(user=self.user)
        
        PointsTransaction.objects.create(customer=self.customer, amount=50, transaction_type='EARN')
        PointsTransaction.objects.create(customer=self.customer, amount=-10, transaction_type='REDEEM')
        
        url = reverse('customer-history', kwargs={'pk': self.customer.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_current_points_is_readonly_manual_update(self):
        self.client.force_authenticate(user=self.user)
        
        url = reverse('customer-detail', kwargs={'pk': self.customer.id})
        data = {
            "current_points": 1000,
            "first_name": "Nombre Hackeado"
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.first_name, "Nombre Hackeado")
        self.assertEqual(self.customer.current_points, 0) 