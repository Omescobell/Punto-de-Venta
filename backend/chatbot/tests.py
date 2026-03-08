from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import ChatBotUsers
from django.utils import timezone

User = get_user_model()


class BaseChatBotTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Usuarios
        self.admin_user = User.objects.create_user(
            email='admin@test.com', username='AdminJuan', password='password123', role='ADMIN'
        )
        self.employee_user = User.objects.create_user(
            email='employee@test.com', username='VendedorPepe', password='password123', role='EMPLOYEE'
        )
        
        # Datos base
        self.valid_payload = {
            'mobile_number': '+521234567890',
            'name': 'Cliente Telegram'
        }
        self.url = '/api/chatbotusers/'


class ChatBotUnitTests(BaseChatBotTestCase):

    def test_mobile_number_is_primary_key(self):
        """
        Valida que el modelo use el mobile_number como PK y no un ID autoincremental.
        """
        ChatBotUsers.objects.create(**self.valid_payload)
        
        # Intentamos recuperar usando el teléfono como ID directo
        user_db = ChatBotUsers.objects.filter(pk=self.valid_payload['mobile_number']).first()
        self.assertIsNotNone(user_db)
        self.assertEqual(user_db.name, 'Cliente Telegram')

class ChatBotIntegrationTests(BaseChatBotTestCase):
    
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)

    def test_last_interaction_field_is_read_only(self):
        """
        Valida que la API ignore intentos de escritura manual en campos protegidos.
        """
        payload_hacker = {
            'mobile_number': '+529999999999',
            'name': 'Hacker',
            'last_interaction': '2050-01-01T12:00:00Z' # Intento de inyección
        }
        
        response = self.client.post(self.url, payload_hacker)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificamos en DB que el campo siga siendo None o el default
        user_created = ChatBotUsers.objects.get(mobile_number='+529999999999')
        self.assertIsNone(user_created.last_interaction)

class ChatBotSecurityTests(BaseChatBotTestCase):

    def test_employee_cannot_create_chatbot_user(self):
        """
        Valida que un empleado NO pueda crear registros (POST).
        """
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ChatBotUsers.objects.count(), 0)

    def test_employee_cannot_list_chatbot_users(self):
        """
        Valida que un empleado NO pueda ver registros (GET).
        """
        self.client.force_authenticate(user=self.employee_user)
        ChatBotUsers.objects.create(**self.valid_payload) # Creado por sistema/admin
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_delete_chatbot_user(self):
        """
        Valida que un empleado NO pueda borrar registros (DELETE).
        """
        self.client.force_authenticate(user=self.employee_user)
        user = ChatBotUsers.objects.create(**self.valid_payload)
        
        url_detail = f"{self.url}{user.mobile_number}/"
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ChatBotValidationTests(BaseChatBotTestCase):
    
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)

    def test_prevent_duplicate_mobile_number(self):
        """
        Valida que la API rechace (400) intentos de duplicar la PK.
        """
        # Primer registro exitoso
        self.client.post(self.url, self.valid_payload)
        
        # Segundo intento con los mismos datos
        response = self.client.post(self.url, self.valid_payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Aseguramos que solo exista 1 registro
        self.assertEqual(ChatBotUsers.objects.filter(mobile_number=self.valid_payload['mobile_number']).count(), 1)

class ChatBotFunctionalTests(BaseChatBotTestCase):
    
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)

    def test_admin_complete_lifecycle_create_and_delete(self):
        """
        Prueba el flujo completo: Admin crea usuario -> Verifica -> Borra usuario.
        """
        # 1. Crear
        response_create = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChatBotUsers.objects.count(), 1)
        
        # 2. Verificar existencia
        created_user = ChatBotUsers.objects.get(pk=self.valid_payload['mobile_number'])
        self.assertEqual(created_user.name, 'Cliente Telegram')
        
        # 3. Eliminar
        # Nota: Asumiendo que el Router usa el mobile_number en la URL
        url_detail = f"{self.url}{created_user.mobile_number}/" 
        response_delete = self.client.delete(url_detail)
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)
        
        # 4. Verificar eliminación
        self.assertEqual(ChatBotUsers.objects.count(), 0)