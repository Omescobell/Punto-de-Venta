from django.db import models
from django.urls import reverse

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=20)
    contact_person = models.CharField(max_length=40)
    rfc = models.CharField(max_length=40)
    tax_address = models.CharField(250)

    def get_absolute_url(self):
        return reverse("supplier_detail", kwargs={"pk": self.pk})
    
    def __str__(self):
        return f"{self.name}, {self.mobile_number}"
    
