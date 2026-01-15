from django.db import models
from django.urls import reverse

class Customer(models.Model):
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    birth_date = models.DateField()
    is_frequent = models.BooleanField(default=False)

    class Meta:
        db_table = 'CUSTOMERS'

    def get_absolute_url(self):
        return reverse("customer_detail", kwargs={"pk": self.pk})
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"