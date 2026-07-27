from django.db import models
from apps.registry.models import File
from apps.accounts.models import Employee

class AIDocumentAnalysis(models.Model):
    file = models.OneToOneField(File, on_delete=models.CASCADE, related_name='ai_analysis')
    predicted_category = models.CharField(max_length=100, blank=True, null=True)
    confidence_score = models.FloatField(default=0.0)
    keywords = models.JSONField(default=list)
    summary = models.TextField(blank=True, null=True)
    sentiment = models.CharField(max_length=20, blank=True, null=True)
    priority_suggestion = models.CharField(max_length=10, blank=True, null=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'ai_analysis'

class FileIntegrity(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='integrity_checks')
    sha256_hash = models.CharField(max_length=64)
    verified = models.BooleanField(default=True)
    checked_at = models.DateTimeField(auto_now_add=True)
    checked_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    class Meta: db_table = 'file_integrity'

class ForensicLog(models.Model):
    SEVERITY = [('LOW','Low'),('MEDIUM','Medium'),('HIGH','High'),('CRITICAL','Critical')]
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='forensic_logs', null=True, blank=True)
    event_type = models.CharField(max_length=50)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY, default='MEDIUM')
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'forensic_logs'; ordering = ['-created_at']

class AnomalyDetection(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='anomalies')
    anomaly_type = models.CharField(max_length=50)
    description = models.TextField()
    risk_score = models.FloatField(default=0.0)
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    class Meta: db_table = 'anomaly_detection'
