from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatBotUsersView

router = DefaultRouter()
router.register(r'chatbotusers', ChatBotUsersView, basename='chatbotuser')

urlpatterns = [
    # Rutas del ViewSet chatbotusers/
    path('', include(router.urls)),
]