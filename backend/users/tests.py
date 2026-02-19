from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

class BaseUserTest(APITestCase):
    def setUp(self):
        # Datos base para todas las pruebas
        self.login_url = '/api/auth/login/'
        self.users_list_url = '/api/users/' 
        self.users_me_url = '/api/users/me/'

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

    def authenticate(self, user):
        """Helper para obtener token e inyectarlo en el cliente"""
        response = self.client.post(self.login_url, {
            'email': user.email,
            'password': 'password123'
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token

class TestNivel1Unitarias(BaseUserTest):
    """
    Se prueban los métodos del modelo y la integridad de datos a bajo nivel.
    """

    def test_model_user_creation_logic(self):
        # RQF: El sistema permite modificar e insertar usuarios
        user = User.objects.create_user(
            email='unit@test.com', 
            password='123', 
            role='EMPLOYEE',
            username = 'employee'
        )
        self.assertEqual(user.email, 'unit@test.com')
        self.assertTrue(user.check_password('123')) # Verifica hash de contraseña
        self.assertTrue(user.is_active) # RQNF: Verifica existencia y activo por defecto

    def test_soft_delete_logic_on_model(self):
        # RQF: El sistema al eliminar un usuario lo marcará como inactivo
        # Probamos la lógica del 'algoritmo' de borrado sin pasar por la API aún.
        user = User.objects.create_user(email='borrar@test.com', password='123',username='elpepe')
        user.is_active = False # Simulamos la lógica de desactivación
        user.save()
        
        refreshed = User.objects.get(id=user.id)
        self.assertFalse(refreshed.is_active)

class TestNivel2Integracion(BaseUserTest):
    """
    Se prueba la comunicación entre URLs, Vistas y Serializers.
    """

    def test_login_interface_connection(self):
        """
        # RQF: El sistema dispone de una ruta para iniciar sesión
        # RQF: Retorna token (relación entre vista de login y JWT)
        """
        
        response = self.client.post(self.login_url, {'email': 'admin@test.com', 'password': 'password123'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data) # Verifica que la interfaz devuelve el contrato correcto

    def test_url_structure_listing(self):
        # RQNF54: Valida estructura de URL /api/users/ para lista completa
        self.authenticate(self.admin_user)
        response = self.client.get(self.users_list_url) # '/api/users/'
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list) # Verifica que devuelve una lista (integración correcta)

class TestNivel3Funcionales(BaseUserTest):
    """
    Se prueban reglas de negocio específicas y restricciones (Permisos, Validaciones).
    """

    def test_employee_cannot_list_users_permission(self):
        # RQNF: El sistema valida la autorización (si falla, rechaza inmediatamente)
        # RQNF: Valida permisos de administrador o dueño
        self.authenticate(self.employee_user)
        response = self.client.get(self.users_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_soft_delete_implementation(self):
        # RQF: El sistema permite eliminar usuarios
        # RQF: Al eliminar lo marca como inactivo (Requisito funcional crítico)
        self.authenticate(self.admin_user)
        url_delete = f'/api/users/{self.employee_user.id}/'
        
        response = self.client.delete(url_delete)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Validación de la regla de negocio en BD
        self.employee_user.refresh_from_db()
        self.assertFalse(self.employee_user.is_active, "El usuario debe estar marcado como inactivo (Soft Delete)")

    def test_update_user_implementation(self):
        # RQF4: El sistema permite modificar usuarios
        self.authenticate(self.admin_user)
        url_update = f'/api/users/{self.employee_user.id}/'
        data = {'first_name': 'NombreCambiado'}
        
        response = self.client.patch(url_update, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'NombreCambiado')

class TestNivel4Sistema(BaseUserTest):
    """
    Pruebas más amplias que verifican el cumplimiento del requerimiento con entradas variadas.
    """

    def test_create_user_system_compliance(self):
        """
        RQF:El sistema permite modificar e insertar usuarios
        El sistema genera y entrega una "credencial digital" temporal 
        Prueba: Crear usuario con campos faltantes opcionales (blank=True)
        Verifica que el sistema completo acepte estas entradas y responda correctamente.
        """
        
        self.authenticate(self.admin_user)
        data = {
            'email': 'nuevo@test.com',
            'username': 'Nuevo',
            'password': '123',
            'first_name': 'SoloNombre',
            'last_name': 'SoloApellido',
            'role': 'EMPLOYEE'
            # Faltan teléfono y dirección
        }
        response = self.client.post(self.users_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['phone_number'], '') # El sistema cumple manejando vacíos

    def test_security_flow_token_validation(self):
        # RQNF: Valida credencial vigente
        # RQNF: Verifica existencia del usuario y activo
        # Simulamos un flujo donde el token es incorrecto
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token_falso_123')
        response = self.client.get(self.users_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class TestNivel5Aceptacion(BaseUserTest):
    """
    Simula lo que el usuario final (Empleado) verifica para aceptar que el módulo funciona.
    """

    def test_user_story_view_own_profile(self):
        """
        Historia de usuario: Como empleado, quiero ver mi perfil con todos mis datos.
        """
        # RQF: El sistema solicita la credencial digital para cualquier acción posterior al inicio de sesión.
        self.authenticate(self.employee_user)
        
        # 2. Consultar perfil (RQF: Ver usuarios / RQNF9: Ver su información)
        response = self.client.get(self.users_me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Validación visual de datos (lo que ve el usuario)
        self.assertEqual(response.data['email'], 'employee@test.com')
        self.assertEqual(response.data['last_name'], 'Gómez')       
        self.assertEqual(response.data['phone_number'], '555-9999') 
        self.assertEqual(response.data['address'], 'Calle Falsa 123')
