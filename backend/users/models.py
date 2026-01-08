from django.db import models
from django.urls import reverse
from datetime import timedelta,timezone

class Users(models.Model):
    name = models.CharField(max_length=150)
    last_name= models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    mobile_number = models.BigIntegerField()
    email = models.CharField(max_length=254)
    address = models.CharField(max_length=200)
    user_role = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    
    def get_absolute_url(self):
        return reverse("users_detail", kwargs={"pk": self.pk})
    
    def __str__(self):
        return self.username
    

def get_expiration_date():
    return timezone.now() + timedelta(days=1)

class RefreshToken(models.Model): 
    token = models.TextField() 
    user_agent = models.CharField(max_length=255) 
    ip_address = models.GenericIPAddressField() 
    expires_at = models.DateTimeField(default=get_expiration_date)
    created_at = models.DateTimeField(default=timezone,auto_now=False,auto_now_add=False) 
    is_revoked = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")