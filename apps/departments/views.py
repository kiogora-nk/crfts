from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.accounts.models import Department, Employee
from .serializers import DepartmentSerializer, EmployeeListSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

class EmployeeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeListSerializer
    permission_classes = [IsAuthenticated]