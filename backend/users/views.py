from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status,viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import MyTokenObtainPairSerializer
from .models import User, RefreshToken
from .serializers import UserSerializer, RefreshTokenSerializer
from .permissions import IsAdminOrOwner


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return  Response({"detail": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)
        
        usuario_obj = serializer.user  
        user_id = usuario_obj
        tokens = serializer.validated_data 
        refresh_token_str = tokens['refresh']
        #Obtener ip
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_addr = x_forwarded_for.split(',')[0]
        else:
            ip_addr = request.META.get('REMOTE_ADDR')
        
        user_agent_str = request.META.get('HTTP_USER_AGENT', '')

        RefreshToken.objects.create(
            user=user_id,
            token=str(tokens['refresh']), 
            user_agent=user_agent_str,
            ip_address=ip_addr,        
        )

        return Response(tokens, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated] 

    def get_permissions(self):
        """
        Define permisos estrictos por acción.
        """
        # Excepción: Un empleado sí puede ver SU propio perfil (endpoint 'me')
        if self.action == 'me':
            return [permissions.IsAuthenticated()]
        
        # SOLO Admin y Owner pasan.
        return [IsAdminOrOwner()]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
    
    #GET /api/users/me/
    @action(detail=False, methods=['get', 'put'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RefreshTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RefreshToken.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        session = self.get_object()
        session.is_revoked = True
        session.save()
        return Response({"status": "Sesión cerrada correctamente"}, status=status.HTTP_200_OK)