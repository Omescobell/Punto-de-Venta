from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet,PromotionViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'promotions', PromotionViewSet, basename='promotion')

urlpatterns = [
    path('', include(router.urls)),
]