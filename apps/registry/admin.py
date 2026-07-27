from django.contrib import admin
from django.utils import timezone
from .models import File, FileDocument, FileMovement, FileCategory
class DocInline(admin.TabularInline):
    model = FileDocument; extra = 0; readonly_fields = ['created_at']
@admin.register(FileCategory)
class CatAdmin(admin.ModelAdmin): list_display = ['code','name']
@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['file_number','subject','status','priority','current_department','current_holder','days_held','expected_return_date']
    search_fields = ['file_number','subject','current_holder__payroll','current_holder__name']
    list_filter = ['status','priority','current_department','is_archived']
    readonly_fields = ['file_number','days_held','created_at','updated_at']
    inlines = [DocInline]
    fieldsets = (
        ('File Info',{'fields':('file_number','subject','description','category')}),
        ('Status & Location',{'fields':('status','priority','department','current_department','current_holder','date_received','days_held')}),
        ('Timeline',{'fields':('expected_return_date','hold_duration_days')}),
        ('Archive',{'fields':('is_archived',)}),
        ('Metadata',{'fields':('created_by','created_at','updated_at')}),
    )
    def save_model(self, request, obj, form, change):
        if not obj.file_number:
            d = obj.department; y = timezone.now().year
            last = File.objects.filter(file_number__startswith=f'CGM-{d.code}-{y}').order_by('-file_number').first()
            n = int(last.file_number.split('-')[-1])+1 if last else 1
            obj.file_number = f'CGM-{d.code}-{y}-{str(n).zfill(6)}'
        if not obj.created_by and hasattr(request.user,'employee') and request.user.employee:
            obj.created_by = request.user.employee
        if not obj.current_holder: obj.current_holder = obj.created_by
        if not obj.current_department: obj.current_department = obj.department
        super().save_model(request, obj, form, change)
@admin.register(FileMovement)
class MoveAdmin(admin.ModelAdmin):
    list_display = ['file','action','to_dept','performed_by','created_at']
    list_filter = ['action']
    readonly_fields = ['created_at']
@admin.register(FileDocument)
class DocAdmin(admin.ModelAdmin):
    list_display = ['name','file','version','uploaded_by','created_at']
