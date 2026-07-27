from django.db import models
from apps.registry.models import File
from apps.accounts.models import Department, Employee
class FileTransfer(models.Model):
    TYPES = [('TRANSFER','Transfer'),('FORWARD','Forward'),('RETURN','Return')]
    STATUS = [('PENDING','Pending'),('RECEIVED','Received'),('REJECTED','Rejected'),('COMPLETED','Completed')]
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='transfers')
    transfer_number = models.CharField(max_length=50, unique=True)
    from_dept = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='transfers_sent')
    to_dept = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='transfers_received')
    from_emp = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='transfers_initiated')
    to_emp = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_assigned')
    transfer_type = models.CharField(max_length=10, choices=TYPES, default='TRANSFER')
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS, default='PENDING')
    transferred_at = models.DateTimeField(auto_now_add=True)
    received_at = models.DateTimeField(null=True, blank=True)
    class Meta: db_table = 'file_transfers'; ordering = ['-transferred_at']
    def __str__(self): return self.transfer_number
