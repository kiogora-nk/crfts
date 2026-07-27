from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
class Department(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.code} - {self.name}'
    class Meta: db_table = 'departments'; verbose_name_plural = 'Departments'
class Role(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    def __str__(self): return self.name
    class Meta: db_table = 'roles'
class Employee(models.Model):
    payroll = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.payroll} - {self.name}'
    class Meta: db_table = 'employees'
class UserManager(BaseUserManager):
    def create_user(self, payroll_number, password=None, **extra):
        if not payroll_number: raise ValueError('Payroll number required')
        user = self.model(payroll_number=payroll_number, **extra)
        user.set_password(password); user.save()
        return user
    def create_superuser(self, payroll_number, password=None, **extra):
        extra.setdefault('is_staff', True); extra.setdefault('is_superuser', True)
        return self.create_user(payroll_number, password, **extra)
class User(AbstractBaseUser, PermissionsMixin):
    employee = models.OneToOneField(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    payroll_number = models.CharField(max_length=20, unique=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = UserManager()
    USERNAME_FIELD = 'payroll_number'
    REQUIRED_FIELDS = []
    def __str__(self): return self.payroll_number
    class Meta: db_table = 'users'
