from rest_framework import serializers
from .models import ChatBotUsers

class ChatBotUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatBotUsers
        fields = ['mobile_number','name','last_interaction']
        extra_kwargs = {
            'last_interaction': {'read_only': True}
        }
