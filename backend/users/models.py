from django.db import models
from django.urls import reverse
from django.utils import timezone 
from datetime import timedelta

class User(models.Model): 
    username = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password_hash = models.CharField(max_length=255) 
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(max_length=254, unique=True) 
    address = models.CharField(max_length=200)

    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('EMPLOYEE', 'Empleado'),
        ('OWNER', 'Dueño'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse("users_detail", kwargs={"pk": self.pk})

def get_expiration_date():
    return timezone.now() + timedelta(days=1)

class RefreshToken(models.Model): 
    token = models.TextField() 
    user_agent = models.CharField(max_length=255) 
    ip_address = models.GenericIPAddressField()
    expires_at = models.DateTimeField(default=get_expiration_date)
    created_at = models.DateTimeField(auto_now_add=True) 
    is_revoked = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")

    def __str__(self):
        return f"Token de {self.user.username}"