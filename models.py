
from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class chat_messages(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    sendtime = models.DateTimeField(auto_now=True)