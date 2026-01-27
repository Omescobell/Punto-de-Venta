from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import ChatBotUsers
from django.utils import timezone

User = get_user_model()

class ChatBotUsersTests(APITestCase):

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            username='AdminJuan',
            password='password123',
            role='ADMIN' 
        )

        self.employee_user = User.objects.create_user(
            email='employee@test.com',
            username='VendedorPepe',
            password='password123',
            role='EMPLOYEE',
            first_name='Pepe',
            last_name='Gómez',          
            phone_number='555-9999',    
            address='Calle Falsa 123'    
        )

        self.client.force_authenticate(user=self.admin_user)

        self.valid_payload = {
            'mobile_number': '+521234567890',
            'name': 'Cliente Telegram'
        }
        self.url = '/api/chatbotusers/' 

    def test_create_chatbot_user_as_admin(self):
        """
        Prueba: Un Admin debe poder registrar un usuario de chatbot.
        """
        response = self.client.post(self.url, self.valid_payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChatBotUsers.objects.count(), 1)
        self.assertEqual(ChatBotUsers.objects.get().name, 'Cliente Telegram')

    def test_mobile_number_is_pk(self):
        """
        Prueba: Verifica que el mobile_number actúa como ID (Primary Key).
        """
        self.client.post(self.url, self.valid_payload)
        
        # Intentamos recuperar usando el teléfono como ID
        user_db = ChatBotUsers.objects.get(pk='+521234567890')
        self.assertIsNotNone(user_db)

    def test_prevent_duplicate_mobile_number(self):
        """
        Prueba: La base de datos debe rechazar duplicados de PK.
        """
        # Primer insert
        self.client.post(self.url, self.valid_payload)
        
        # Segundo insert idéntico
        response = self.client.post(self.url, self.valid_payload)
        
        # Debe fallar (400 Bad Request por validación de unicidad)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_last_interaction_is_read_only(self):
        """
        Prueba CRÍTICA: El campo last_interaction no debe poder editarse vía API
        directamente en el POST/PUT (read_only=True en serializer).
        """
        payload_hacker = {
            'mobile_number': '+529999999999',
            'name': 'Hacker',
            # Intentamos forzar una fecha
            'last_interaction': '2050-01-01T12:00:00Z' 
        }
        
        response = self.client.post(self.url, payload_hacker)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificamos que en la BD se guardó como NULL (o default), ignorando el dato enviado
        user_created = ChatBotUsers.objects.get(mobile_number='+529999999999')
        self.assertIsNone(user_created.last_interaction)

    def test_delete_chatbot_user(self):
        """
        Prueba: Un Admin puede borrar un usuario de chatbot.
        """
        # Crear primero
        self.client.post(self.url, self.valid_payload)
        
        # URL específica del recurso (Detail View)
        # Nota: Al ser el teléfono la PK, la URL será .../users/+521234.../
        url_detail = f"{self.url}{self.valid_payload['mobile_number']}/"
        
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ChatBotUsers.objects.count(), 0)

    def test_employee_cannot_access_chatbot_users(self):
        """
        Prueba de Seguridad: Un usuario con rol 'EMPLOYEE' NO debe poder
        crear, editar ni ver usuarios del chatbot. Debe recibir 403 Forbidden.
        """
        # 1. Autenticamos como el empleado (VendedorPepe)
        self.client.force_authenticate(user=self.employee_user)
        
        # 2. Intentamos CREAR (POST)
        response_create = self.client.post(self.url, self.valid_payload)
        
        # Esperamos que sea RECHAZADO (403)
        self.assertEqual(response_create.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verificamos que NO se creó nada en la BD
        self.assertEqual(ChatBotUsers.objects.count(), 0)

        # 3. Intentamos LISTAR (GET) para asegurar que no pueda ni verlos
        response_list = self.client.get(self.url)
        self.assertEqual(response_list.status_code, status.HTTP_403_FORBIDDEN)