from django.db import models

class ChatBotUsers(models.Model):
    mobile_number = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    last_interaction = models.DateTimeField(blank=True,default=None,null=True)

    class Meta:
        db_table = 'CHATBOT_USERS'