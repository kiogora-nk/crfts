from django.db import models
from apps.accounts.models import User
from apps.registry.models import File
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30)
    message = models.TextField()
    file = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'notifications'; ordering = ['-created_at']
