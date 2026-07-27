from django.db import models
from django.utils import timezone
from apps.accounts.models import Department, Employee
class FileCategory(models.Model):
    name = models.CharField(max_length=100); code = models.CharField(max_length=20, unique=True)
    def __str__(self): return self.name
    class Meta: db_table = 'file_categories'; verbose_name_plural = 'File Categories'
class File(models.Model):
    PRIORITY = [('LOW','Low'),('MEDIUM','Medium'),('HIGH','High'),('URGENT','Urgent')]
    STATUS = [('REGISTERED','Registered'),('RECEIVED','Received'),('UNDER_REVIEW','Under Review'),('PENDING_APPROVAL','Pending Approval'),('APPROVED','Approved'),('RETURNED','Returned'),('TRANSFERRED','Transferred'),('COMPLETED','Completed'),('ARCHIVED','Archived')]
    file_number = models.CharField(max_length=30, unique=True, db_index=True)
    subject = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(FileCategory, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='files_owned')
    current_department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='files_current')
    current_holder = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='files_held')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS, default='REGISTERED')
    created_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='files_created')
    date_received = models.DateTimeField(default=timezone.now)
    days_held = models.IntegerField(default=0)
    expected_return_date = models.DateTimeField(null=True, blank=True)
    hold_duration_days = models.IntegerField(default=7)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if self.date_received: self.days_held = (timezone.now() - self.date_received).days
        super().save(*args, **kwargs)
    def __str__(self): return self.file_number
    class Meta: db_table = 'files'; ordering = ['-created_at']
class FileDocument(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=255); path = models.CharField(max_length=500)
    version = models.IntegerField(default=1); uploaded_by = models.ForeignKey(Employee, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'file_documents'
class FileMovement(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='movements')
    from_dept = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_from')
    to_dept = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_to')
    action = models.CharField(max_length=100); remarks = models.TextField(blank=True, null=True)
    report = models.TextField(blank=True, null=True)
    hold_days = models.IntegerField(default=7)
    performed_by = models.ForeignKey(Employee, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'file_movements'; ordering = ['-created_at']
