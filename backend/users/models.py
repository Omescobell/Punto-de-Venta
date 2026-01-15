from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.urls import reverse
from django.utils import timezone 
from datetime import timedelta
from django.conf import settings

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        
        user.set_password(password) 
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN') # Forzamos rol admin
        
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin): 
    #La clase AbstractBaseUser ya trae los campos: 'id', 'password', 'last_login'
    #La clase PermissionsMixin trae: 'is_superuser', grupos y permisos
    
    username = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, unique=True) 
    
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=200, blank=True)

    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('EMPLOYEE', 'Empleado'),
        ('OWNER', 'Dueño'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='EMPLOYEE')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) # Necesario para entrar al Admin de Django

    # Configuración del sistema de Auth
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['username'] # Pide el nombre al crear superuser

    class Meta:
        db_table = 'USERS'

    def __str__(self):
        return self.emai

    def get_absolute_url(self):
        return reverse("user_detail", kwargs={"pk": self.pk})

def get_expiration_date():
    return timezone.now() + timedelta(days=1) 

class RefreshToken(models.Model): 
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions")
    
    token = models.TextField()
    user_agent = models.CharField(max_length=255) 
    ip_address = models.GenericIPAddressField()
    expires_at = models.DateTimeField(default=get_expiration_date)
    created_at = models.DateTimeField(auto_now_add=True) 
    is_revoked = models.BooleanField(default=False)

    class Meta:
        db_table = 'REFRESH_TOKENS'

    def __str__(self):
        return f"Sesión de {self.user.username} - {self.created_at}"