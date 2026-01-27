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
    
    def test_customer_becomes_frequent_based_on_last_month(self):
        import calendar
        from datetime import datetime, timedelta 
        from django.utils import timezone
        from orders.models import Order

        self.customer.orders.all().delete()

        today = timezone.now().date()
        first_day_current = today.replace(day=1) 
        last_day_prev = first_day_current - timedelta(days=1)
        first_day_prev = last_day_prev.replace(day=1)

        #Obtener las semanas reales de ese mes
        weeks = calendar.monthcalendar(first_day_prev.year, first_day_prev.month)
        
        orders_created = []

        for week in weeks:
        # Buscamos un día válido en esa semana (los 0 son relleno de otro mes)
            day = next(d for d in week if d != 0)
        
            # Construimos la fecha y luego la hacemos aware
            naive_date = datetime(first_day_prev.year, first_day_prev.month, day)
            date_sim = timezone.make_aware(naive_date)
    
            order = Order.objects.create(
                ticket_folio=f"OLD-{date_sim.day}",
                total=100,
                status='PAID',
                customer=self.customer,
                seller=self.user,
                payment_method='CASH'
            )
        

            Order.objects.filter(pk=order.pk).update(created_at=date_sim)
            order.refresh_from_db()

            orders_created.append(order)

        #Verificación
        
        self.customer.refresh_from_db() 
        es_frecuente = self.customer.update_frequent_status()

        self.assertTrue(es_frecuente, f"Falló: El mes tuvo {len(weeks)} semanas y no se detectaron todas.")

        #Verificar que se actualizó la fecha de chequeo
        today = timezone.now().date()
        self.assertEqual(
            self.customer.last_status_check, 
            today, 
            "Error: El campo last_status_check no se actualizó a la fecha de hoy."
        )
        # Verificar que la función NO recalcula si se llama por segunda vez hoy
        
        if len(orders_created) > 1:
            orders_created[1].delete() 
        else:
            orders_created[0].delete()
        
        resultado_cache = self.customer.update_frequent_status()
        self.assertTrue(resultado_cache, "Falló la optimización: Recalculó a pesar de tener fecha actualizada.")

        # Forzar recalculo para verificar
        self.customer.last_status_check = None
        self.customer.save()


        # Ahora sí debe darse cuenta de que falta una orden
        resultado_recalculado = self.customer.update_frequent_status()
        
        self.assertFalse(resultado_recalculado, "Error: Al borrar una orden y resetear la fecha, debió perder el estatus.")