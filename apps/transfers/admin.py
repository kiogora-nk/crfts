from django.contrib import admin
from .models import *
@admin.register(FileTransfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ['transfer_number','file','from_dept','to_dept','transfer_type','status','transferred_at']
    search_fields = ['transfer_number','file__file_number']
    list_filter = ['transfer_type','status']
