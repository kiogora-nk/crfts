from django.db import models
from apps.accounts.models import User
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payroll = models.CharField(max_length=20)
    action = models.CharField(max_length=100)
    module = models.CharField(max_length=50, blank=True, null=True)
    details = models.JSONField(default=dict)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'audit_logs'; ordering = ['-created_at']
