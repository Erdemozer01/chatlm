# llm/models.py
from django.db import models
import uuid
from django.contrib.auth import get_user_model
# Make sure you import get_user_model if you haven't already
User = get_user_model()

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # user alanı artık zorunlu (null=False, blank=False)
    # Eğer anonim sohbetlere İZİN VERECEKSENİZ null=True, blank=True kalabilir.
    # Şimdilik zorunlu varsayalım:
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Make sure this is added from previous step

    # title = models.CharField(max_length=200, blank=True) # Opsiyonel başlık

    def __str__(self):
        return f"Conversation {self.id} for User {self.user.username}"

class ChatMessage(models.Model):
    # Bu model genellikle değişmez, Conversation'a bağlı kalır
    SENDER_CHOICES = [
        ('human', 'Human'),
        ('ai', 'AI'),
    ]
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.CharField(max_length=50)  # 'human' or 'ai'
    content = models.TextField()  # <<< Add this line if it's missing
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']  # Order messages within a conversation

    def __str__(self):
        return f"{self.sender} at {self.timestamp}: {self.content[:50]}..."