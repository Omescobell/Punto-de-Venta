from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import RefreshToken

User = get_user_model()

class AuthAndUserTests(APITestCase):

    def setUp(self):
        # 1. Admin (Datos básicos)
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            username='AdminJuan',
            password='password123',
            role='ADMIN'
        )

        # 2. Empleado
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

        self.login_url = '/api/auth/login/'
        self.users_list_url = '/api/users/'
        self.users_me_url = '/api/users/me/'

    def authenticate(self, user):
        response = self.client.post(self.login_url, {
            'email': user.email,
            'password': 'password123'
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token

    # --- TESTS ---

    def test_employee_can_see_own_profile_full_data(self):
        """
        Prueba que el empleado vea su perfil CON todos los campos
        """
        self.authenticate(self.employee_user)
        
        response = self.client.get(self.users_me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Validamos que los datos vengan en el JSON
        self.assertEqual(response.data['email'], 'employee@test.com')
        self.assertEqual(response.data['last_name'], 'Gómez')       
        self.assertEqual(response.data['phone_number'], '555-9999') 
        self.assertEqual(response.data['address'], 'Calle Falsa 123') 

    def test_create_user_with_missing_fields(self):
        """
        Prueba: Crear usuario sin teléfono ni dirección (debería funcionar porque son blank=True)
        """
        self.authenticate(self.admin_user)
        data = {
            'email': 'nuevo@test.com',
            'username': 'Nuevo',
            'password': '123',
            'first_name': 'SoloNombre',
            'last_name': 'SoloApellido',
            'role': 'EMPLOYEE'
        }
        response = self.client.post(self.users_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['phone_number'], '') # Debería ser string vacío

    def test_login_success(self):
        response = self.client.post(self.login_url, {'email': 'admin@test.com', 'password': 'password123'})
        self.assertEqual(response.status_code, 200)

    def test_employee_cannot_list_users(self):
        self.authenticate(self.employee_user)
        response = self.client.get(self.users_list_url)
        self.assertEqual(response.status_code, 403)
    
    def test_update_user(self):
        """
        Prueba editar (PATCH) un usuario.
        """
        self.authenticate(self.admin_user)
        
        url_update = f'/api/users/{self.employee_user.id}/'
        data = {'first_name': 'NombreCambiado'}
        
        response = self.client.patch(url_update, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'NombreCambiado')
        
        # Verificamos en base de datos
        self.employee_user.refresh_from_db()
        self.assertEqual(self.employee_user.first_name, 'NombreCambiado')

    def test_soft_delete_user(self):
        """
        Prueba CRÍTICA: Verificar que el DELETE no borra el registro,
        sino que pone is_active = False.
        """
        self.authenticate(self.admin_user)
        
        url_delete = f'/api/users/{self.employee_user.id}/'
        
        response = self.client.delete(url_delete)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        #El usuario TODAVÍA debe existir en la BD
        user_db = User.objects.get(id=self.employee_user.id)
        #Pero debe estar desactivado
        self.assertFalse(user_db.is_active)