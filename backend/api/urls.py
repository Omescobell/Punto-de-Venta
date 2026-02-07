from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
#urls apps
from users.urls import router as users_router
from suppliers.urls import router as suppliers_router
from customers.urls import router as customer_router
from products.urls import router as products_router
from orders.urls import router as orders_router
from chatbot.urls import router as chatbot_router

from rest_framework_simplejwt.views import TokenRefreshView
from users.views import MyTokenObtainPairView

master_router = DefaultRouter()

master_router.registry.extend(users_router.registry)
master_router.registry.extend(suppliers_router.registry)
master_router.registry.extend(customer_router.registry)
master_router.registry.extend(products_router.registry)
master_router.registry.extend(orders_router.registry)
master_router.registry.extend(chatbot_router.registry)

urlpatterns = [
    path('admin/', admin.site.urls),
    #Ruta maestra con todas las rutas de las apps (users,suppliers,customers,products)
    path('api/', include(master_router.urls)),

    path('api-auth/', include('rest_framework.urls')),
    path('auth/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]