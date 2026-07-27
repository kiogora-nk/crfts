from django.contrib import admin
from .models import *
@admin.register(AuditLog)
class AuditAdmin(admin.ModelAdmin):
    list_display = ['payroll','action','module','created_at']
    list_filter = ['action','module']; readonly_fields = ['created_at']
    def has_add_permission(self, request): return False
