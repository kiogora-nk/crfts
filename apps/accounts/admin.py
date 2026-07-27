from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
@admin.register(Department)
class DeptAdmin(admin.ModelAdmin):
    list_display = ['code','name','active']; search_fields = ['code','name']
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['code','name']
@admin.register(Employee)
class EmpAdmin(admin.ModelAdmin):
    list_display = ['payroll','name','department','email','active']
    search_fields = ['payroll','name','email']; list_filter = ['department','active']
@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ['payroll_number','role','is_active','is_staff']
    search_fields = ['payroll_number']
    ordering = ['payroll_number']
    fieldsets = ((None,{'fields':('payroll_number','password')}),('Info',{'fields':('employee','role')}),('Permissions',{'fields':('is_active','is_staff','is_superuser','groups','user_permissions')}))
    add_fieldsets = ((None,{'classes':('wide',),'fields':('payroll_number','password1','password2')}),)
