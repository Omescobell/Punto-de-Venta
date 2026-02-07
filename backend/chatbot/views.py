from rest_framework import viewsets, permissions
from .models import ChatBotUsers
from .serializers import ChatBotUsersSerializer
from .permissions import IsAdminOrOwner

class ChatBotUsersView(viewsets.ModelViewSet):
    queryset = ChatBotUsers.objects.all()
    serializer_class = ChatBotUsersSerializer
    
    def get_permissions(self):
        return [IsAdminOrOwner()]