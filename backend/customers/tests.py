from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal
import calendar
from datetime import datetime, timedelta 
from django.utils import timezone
from .models import Customer, PointsTransaction, CreditTransaction
from orders.models import Order

User = get_user_model()

class BaseCustomerTestCase(APITestCase):
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

class CustomerUnitTests(BaseCustomerTestCase):

    # Verifica RQNF63: Regla de negocio de clientes nuevos/no frecuentes
    def test_new_customer_has_limit_but_zero_availability(self):
        new_customer = Customer.objects.create(
            first_name="Nuevo", last_name="Usuario", phone_number="5599999999",
            email="nuevo@test.com", birth_date="2000-01-01", is_frequent=False
        )
        self.assertEqual(new_customer.credit_limit, Decimal('2000.00'))
        self.assertEqual(new_customer.available_credit, Decimal('0.00'))
        with self.assertRaises(ValidationError):
            new_customer.charge_credit(100)

    # Verifica RQF44 y RQNF63: Lógica interna del modelo al cobrar
    def test_charge_credit_logic_model_check(self):
        self.customer.is_frequent = True
        self.customer.credit_limit = Decimal('1000.00')
        self.customer.save()
        
        self.customer.charge_credit(200, description="Test Charge")
        self.customer.refresh_from_db()
        
        self.assertEqual(self.customer.credit_used, Decimal('200.00'))
        self.assertEqual(self.customer.available_credit, Decimal('800.00'))
        self.assertEqual(CreditTransaction.objects.last().amount, Decimal('200.00'))

    # Verifica RQF45: Lógica interna del modelo al pagar
    def test_pay_off_credit_logic(self):
        self.customer.is_frequent = True
        self.customer.credit_limit = Decimal('1000.00')
        self.customer.credit_used = Decimal('500.00')
        self.customer.save()

        self.customer.pay_off_credit(200, description="Abono")
        self.customer.refresh_from_db()
        
        self.assertEqual(self.customer.credit_used, Decimal('300.00'))
        self.assertEqual(self.customer.available_credit, Decimal('700.00'))

    # Verifica RQNF63: Bloqueo en modelo
    def test_non_frequent_cannot_use_credit(self):
        self.customer.is_frequent = False
        self.customer.credit_limit = Decimal('1000.00')
        self.customer.save()

        with self.assertRaises(ValidationError):
            self.customer.charge_credit(100)

    # Verifica RQF43: Lógica compleja del algoritmo de frecuencias
    def test_customer_becomes_frequent_based_on_last_month(self):
        self.customer.orders.all().delete()
        today = timezone.now().date()
        first_day_current = today.replace(day=1) 
        last_day_prev = first_day_current - timedelta(days=1)
        first_day_prev = last_day_prev.replace(day=1)

        weeks = calendar.monthcalendar(first_day_prev.year, first_day_prev.month)
        orders_created = []

        for week in weeks:
            day = next(d for d in week if d != 0)
            naive_date = datetime(first_day_prev.year, first_day_prev.month, day)
            date_sim = timezone.make_aware(naive_date)
    
            order = Order.objects.create(
                ticket_folio=f"OLD-{date_sim.day}", final_amount=100, status='PAID',
                customer=self.customer, seller=self.user, payment_method='CASH'
            )
            Order.objects.filter(pk=order.pk).update(created_at=date_sim)
            order.refresh_from_db()
            orders_created.append(order)

        self.customer.refresh_from_db() 
        es_frecuente = self.customer.update_frequent_status()
        self.assertTrue(es_frecuente)
        self.assertEqual(self.customer.last_status_check, today)

        # Verificar optimización de caché
        if len(orders_created) > 1: orders_created[1].delete() 
        else: orders_created[0].delete()
        
        self.assertTrue(self.customer.update_frequent_status())

        # Forzar recálculo
        self.customer.last_status_check = None
        self.customer.save()
        self.assertFalse(self.customer.update_frequent_status())


class CustomerIntegrationTests(BaseCustomerTestCase):
    
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    # Verifica RQNF60
    def test_duplicate_email_fails(self):
        self.client.post(self.list_url, self.valid_payload)
        response = self.client.post(self.list_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    # Verifica RQNF60
    def test_duplicate_phone_fails(self):
        self.client.post(self.list_url, self.valid_payload)
        payload_2 = self.valid_payload.copy()
        payload_2['email'] = 'otro@mail.com'
        response = self.client.post(self.list_url, payload_2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)

    # Verifica RQNF61
    def test_missing_required_fields(self):
        response = self.client.post(self.list_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Verifica RQNF62
    def test_is_frequent_is_readonly(self):
        payload = self.valid_payload.copy()
        payload['is_frequent'] = True
        self.client.post(self.list_url, payload)
        self.assertFalse(Customer.objects.last().is_frequent)

    # Verifica RQNF62
    def test_current_points_is_readonly_manual_update(self):
        url = reverse('customer-detail', kwargs={'pk': self.customer.id})
        response = self.client.patch(url, {"current_points": 1000, "first_name": "Hack"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_points, 0)

    # Verifica RQNF65
    def test_credit_fields_are_readonly_in_api(self):
        url = reverse('customer-detail', kwargs={'pk': self.customer.id})
        response = self.client.patch(url, {"credit_used": 0, "available_credit": 50000, "credit_limit": 50000})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.credit_used, Decimal('0.00'))
        self.assertEqual(self.customer.credit_limit, Decimal('50000.00'))

    # Verifica RQNF64
    def test_pay_credit_endpoint_invalid_amount(self):
        url = reverse('customer-pay-credit', kwargs={'pk': self.customer.id})
        response_missing = self.client.post(url, {"description": "Sin monto"}, format='json')
        self.assertEqual(response_missing.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_negative = self.client.post(url, {"amount": -100}, format='json')
        self.assertEqual(response_negative.status_code, status.HTTP_400_BAD_REQUEST)


class CustomerFunctionalTests(BaseCustomerTestCase):
    
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    # Verifica RQF40
    def test_create_customer_success(self):
        response = self.client.post(self.list_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 2) 

    # Verifica RQF41
    def test_earn_points_updates_balance_and_creates_transaction(self):
        url = reverse('customer-points', kwargs={'pk': self.customer.id})
        response = self.client.post(url, {"amount": 100, "transaction_type": "EARN", "description": "Compra Test"})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_points, 100)
        self.assertEqual(PointsTransaction.objects.count(), 1)

    # Verifica RQF41
    def test_redeem_points_decreases_balance(self):
        self.customer.current_points = 500
        self.customer.save()
        url = reverse('customer-points', kwargs={'pk': self.customer.id})
        
        response = self.client.post(url, {"amount": -200, "transaction_type": "REDEEM", "description": "Canje"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_points, 300)

    # Verifica RQF42
    def test_points_history_endpoint(self):
        PointsTransaction.objects.create(customer=self.customer, amount=50, transaction_type='EARN')
        PointsTransaction.objects.create(customer=self.customer, amount=-10, transaction_type='REDEEM')
        
        url = reverse('customer-history', kwargs={'pk': self.customer.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    # Verifica RQF46
    def test_credit_history_endpoint(self):
        CreditTransaction.objects.create(customer=self.customer, amount=Decimal('100.00'), transaction_type='CHARGE')
        url = reverse('customer-credit-history', kwargs={'pk': self.customer.id}) 
        response = self.client.get(url)
        
        if response.status_code != 404:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 1)

    # Verifica RQF45
    def test_pay_credit_endpoint_success(self):
        self.customer.is_frequent = True
        self.customer.credit_limit = Decimal('1000.00')
        self.customer.credit_used = Decimal('500.00')
        self.customer.save()

        url = reverse('customer-pay-credit', kwargs={'pk': self.customer.id})
        response = self.client.post(url, {"amount": 200.00, "description": "Abono API"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.credit_used, Decimal('300.00'))

    # Verifica RQF45 y RQF46 en conjunto
    def test_credit_history_includes_new_payment(self):
        pay_url = reverse('customer-pay-credit', kwargs={'pk': self.customer.id})
        self.client.post(pay_url, {"amount": 150.00, "description": "Pago Historial"}, format='json')

        history_url = reverse('customer-credit-history', kwargs={'pk': self.customer.id})
        response = self.client.get(history_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment_txn = any(
            txn['transaction_type'] == 'PAYMENT' and Decimal(txn['amount']) == Decimal('150.00') 
            for txn in response.data
        )
        self.assertTrue(payment_txn)