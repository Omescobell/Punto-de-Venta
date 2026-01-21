from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')

urlpatterns = [
    # Rutas del ViewSet customers/
    path('', include(router.urls)),
]