from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from apps.registry.models import File, FileMovement, FileCategory, FileDocument
from apps.accounts.models import Department, Employee, User, Role
from apps.transfers.models import FileTransfer
from apps.notifications.models import Notification
from apps.audit.models import AuditLog
import os, random
from django.conf import settings
from django.core.paginator import Paginator

def generate_captcha():
    a = random.randint(1, 10); b = random.randint(1, 10)
    op = random.choice(['+', '-'])
    answer = a + b if op == '+' else a - b
    return f'{a} {op} {b} = ?', str(answer)

def get_emp(user):
    if hasattr(user, 'employee') and user.employee: return user.employee
    emp, created = Employee.objects.get_or_create(payroll=user.payroll_number, defaults={'name': user.payroll_number, 'department': Department.objects.first() or Department.objects.create(code='DEF', name='Default'), 'email': f'{user.payroll_number}@county.go.ke'})
    if created: user.employee = emp; user.save()
    return emp

def get_notif_count(user):
    return Notification.objects.filter(user=user, is_read=False).count()

def is_admin_user(user):
    if not user.is_authenticated: return False
    if user.is_superuser: return True
    if hasattr(user, 'role') and user.role and user.role.code == 'ADMIN': return True
    return False

def login_view(request):
    if request.user.is_authenticated: return redirect('/')
    error = ''
    if request.method == 'POST':
        user_answer = request.POST.get('captcha_answer', '').strip()
        correct_answer = request.POST.get('captcha_correct', '')
        if user_answer == correct_answer:
            u = authenticate(username=request.POST.get('payroll'), password=request.POST.get('password'))
            if u:
                login(request, u)
                AuditLog.objects.create(user=u, payroll=u.payroll_number, action='LOGIN', module='Auth', ip=request.META.get('REMOTE_ADDR'))
                return redirect('/')
            error = 'Invalid payroll number or password'
        else:
            error = 'Wrong math answer. Please try again.'
    question, answer = generate_captcha()
    return render(request, 'accounts/login.html', {'error': error, 'captcha_question': question, 'captcha_answer': answer})

def logout_view(request):
    if request.user.is_authenticated:
        AuditLog.objects.create(user=request.user, payroll=request.user.payroll_number, action='LOGOUT', module='Auth')
    logout(request)
    return redirect('/login/')

def password_reset(request):
    msg = ''
    if request.method == 'POST':
        payroll = request.POST.get('payroll', '').strip()
        try:
            u = User.objects.get(payroll_number=payroll)
            if u.employee and u.employee.email:
                msg = f'Password reset link sent to {u.employee.email}. Contact ICT if you don\'t receive it.'
            else:
                msg = 'No email on file. Please contact ICT Department for password reset.'
        except User.DoesNotExist:
            msg = 'If this payroll exists, reset instructions have been sent.'
    return render(request, 'accounts/password_reset.html', {'msg': msg})

@login_required(login_url='/login/')
def home_redirect(request):
    if is_admin_user(request.user): return admin_dashboard(request)
    return user_dashboard(request)

@login_required(login_url='/login/')
def admin_dashboard(request):
    total = File.objects.filter(is_archived=False).count()
    completed = File.objects.filter(status='COMPLETED', is_archived=False).count()
    pending_transfers = FileTransfer.objects.filter(status='PENDING').count()
    overdue = File.objects.filter(expected_return_date__date__lt=timezone.now().date(), status__in=['RECEIVED','UNDER_REVIEW'], is_archived=False).count()
    recent = File.objects.filter(is_archived=False).select_related('current_department','current_holder').order_by('-created_at')[:10]
    return render(request, 'registry/dashboard.html', {
        'total': total, 'completed': completed, 'pending': pending_transfers, 'overdue': overdue,
        'files': recent, 'user': request.user, 'notif_count': get_notif_count(request.user), 'recent_notifications': Notification.objects.all().order_by('-created_at')[:5]
    })

@login_required(login_url='/login/')
def user_dashboard(request):
    emp = get_emp(request.user)
    dept = emp.department
    my_files = File.objects.filter(current_holder=emp, is_archived=False).select_related('current_department').order_by('-created_at')
    dept_files = File.objects.filter(current_department=dept, is_archived=False).exclude(current_holder=emp).select_related('current_holder').order_by('-created_at')[:20]
    pending_transfers = FileTransfer.objects.filter(to_emp=emp, status='PENDING').select_related('file','from_dept').order_by('-transferred_at')
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10]
    return render(request, 'registry/my_dashboard.html', {
        'my_files': my_files, 'dept_files': dept_files, 'pending': pending_transfers,
        'notifications': notifications, 'user': request.user, 'employee': emp,
        'notif_count': get_notif_count(request.user)
    })

@login_required(login_url='/login/')
def file_list(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    dept_filter = request.GET.get('dept', '')
    page = request.GET.get('page', 1)
    if is_admin_user(request.user):
        files = File.objects.filter(is_archived=False)
    else:
        emp = get_emp(request.user)
        files = File.objects.filter(is_archived=False).filter(Q(current_holder=emp) | Q(current_department=emp.department)).distinct()
    files = files.select_related('current_department','current_holder','category')
    if q: files = files.filter(Q(file_number__icontains=q) | Q(subject__icontains=q) | Q(current_holder__payroll__icontains=q) | Q(current_holder__name__icontains=q))
    if status_filter: files = files.filter(status=status_filter)
    if dept_filter: files = files.filter(current_department_id=dept_filter)
    files = files.order_by('-created_at')
    paginator = Paginator(files, 20)
    page_obj = paginator.get_page(page)
    return render(request, 'registry/file_list.html', {
        'files': page_obj, 'q': q, 'status_filter': status_filter,
        'dept_filter': dept_filter, 'departments': Department.objects.filter(active=True),
        'user': request.user, 'notif_count': get_notif_count(request.user)
    })

@login_required(login_url='/login/')
def register_file(request):
    depts = Department.objects.filter(active=True)
    cats = FileCategory.objects.all()
    if request.method == 'POST':
        d = Department.objects.get(id=request.POST['dept'])
        y = timezone.now().year
        last = File.objects.filter(file_number__startswith=f'CGM-{d.code}-{y}').order_by('-file_number').first()
        n = int(last.file_number.split('-')[-1]) + 1 if last else 1
        fn = f'CGM-{d.code}-{y}-{str(n).zfill(6)}'
        emp = get_emp(request.user)
        f = File.objects.create(file_number=fn, subject=request.POST['subject'].strip(), description=request.POST.get('description','').strip(), department=d, current_department=d, category_id=request.POST.get('category') or None, priority=request.POST.get('priority','MEDIUM'), created_by=emp, current_holder=emp)
        FileMovement.objects.create(file=f, to_dept=d, action='File Registered', remarks='Created in system', performed_by=emp)
        AuditLog.objects.create(user=request.user, payroll=request.user.payroll_number, action='FILE_REGISTERED', module='Registry', details={'file_number': fn})
        dept_emps = Employee.objects.filter(department=d, active=True)
        for e in dept_emps:
            if hasattr(e, 'user') and e.user:
                Notification.objects.create(user=e.user, notification_type='NEW_FILE', message=f'New file {fn}: "{f.subject}" registered in {d.name}', file=f)
        if request.FILES.get('document'):
            doc = request.FILES['document']; file_dir = os.path.join(settings.MEDIA_ROOT, 'documents', fn); os.makedirs(file_dir, exist_ok=True)
            with open(os.path.join(file_dir, doc.name), 'wb+') as dest:
                for chunk in doc.chunks(): dest.write(chunk)
            FileDocument.objects.create(file=f, name=doc.name, path=f'documents/{fn}/{doc.name}', uploaded_by=emp)
        return redirect('/files/')
    return render(request, 'registry/register_file.html', {'departments': depts, 'categories': cats, 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def file_detail(request, pk):
    f = File.objects.select_related('current_department','current_holder','category','department','created_by').get(id=pk)
    moves = FileMovement.objects.filter(file=f).select_related('to_dept','performed_by').order_by('-created_at')
    docs = FileDocument.objects.filter(file=f)
    return render(request, 'registry/file_detail.html', {'file': f, 'movements': moves, 'documents': docs, 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def file_tracking(request, pk):
    f = File.objects.get(id=pk)
    moves = FileMovement.objects.filter(file=f).select_related('to_dept','from_dept','performed_by').order_by('created_at')
    return render(request, 'registry/tracking.html', {'file': f, 'movements': moves, 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def upload_document(request, pk):
    f = File.objects.get(id=pk)
    if request.method == 'POST' and request.FILES.get('doc'):
        doc = request.FILES['doc']; file_dir = os.path.join(settings.MEDIA_ROOT, 'documents', f.file_number); os.makedirs(file_dir, exist_ok=True)
        with open(os.path.join(file_dir, doc.name), 'wb+') as dest:
            for chunk in doc.chunks(): dest.write(chunk)
        emp = get_emp(request.user)
        FileDocument.objects.create(file=f, name=doc.name, path=f'documents/{f.file_number}/{doc.name}', uploaded_by=emp)
        FileMovement.objects.create(file=f, action='Document Uploaded', remarks=doc.name, performed_by=emp)
        return redirect(f'/file/{pk}/')
    return render(request, 'registry/upload_document.html', {'file': f, 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def download_document(request, pk, doc_id):
    doc = FileDocument.objects.get(id=doc_id, file_id=pk)
    file_path = os.path.join(settings.MEDIA_ROOT, doc.path)
    if os.path.exists(file_path):
        from django.http import FileResponse
        return FileResponse(open(file_path, 'rb'), filename=doc.name)
    return redirect(f'/file/{pk}/')

@login_required(login_url='/login/')
def delete_file(request, pk):
    f = File.objects.get(id=pk)
    emp = get_emp(request.user)
    if f.created_by == emp or is_admin_user(request.user):
        f.is_archived = True; f.status = 'ARCHIVED'; f.save()
        FileMovement.objects.create(file=f, action='File Deleted/Archived', remarks=f'Deleted by {emp.name}', performed_by=emp)
        AuditLog.objects.create(user=request.user, payroll=request.user.payroll_number, action='FILE_DELETED', module='Registry', details={'file_number': f.file_number})
        return redirect('/files/')
    return redirect(f'/file/{pk}/')

@login_required(login_url='/login/')
def request_file(request):
    depts = Department.objects.filter(active=True)
    emps = Employee.objects.filter(active=True).select_related('department')
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        from_dept_id = request.POST.get('from_dept')
        from_emp_id = request.POST.get('from_emp') or None
        emp = get_emp(request.user)
        if from_emp_id:
            try:
                to_user = User.objects.get(employee_id=from_emp_id)
                Notification.objects.create(user=to_user, notification_type='FILE_REQUEST', message=f'FILE REQUEST from {emp.name} ({emp.department.name}): {subject}', file=None)
            except: pass
        else:
            dept_emps = Employee.objects.filter(department_id=from_dept_id, active=True)
            for e in dept_emps:
                if hasattr(e, 'user') and e.user:
                    Notification.objects.create(user=e.user, notification_type='FILE_REQUEST', message=f'FILE REQUEST from {emp.name} ({emp.department.name}): {subject}', file=None)
        return redirect('/files/')
    return render(request, 'registry/request_file.html', {'departments': depts, 'employees': emps, 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def admin_reset_password(request):
    if not is_admin_user(request.user): return redirect('/')
    msg = ''
    if request.method == 'POST':
        payroll = request.POST.get('payroll', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        try:
            u = User.objects.get(payroll_number=payroll)
            u.set_password(new_password); u.save()
            msg = f'Password for {payroll} has been reset to: {new_password}'
            AuditLog.objects.create(user=request.user, payroll=request.user.payroll_number, action='PASSWORD_RESET', module='Admin', details={'reset_for': payroll})
        except User.DoesNotExist:
            msg = 'User not found'
    return render(request, 'admin/admin_reset_password.html', {'msg': msg, 'user': request.user})

@login_required(login_url='/login/')
def transfer_list(request):
    emp = get_emp(request.user)
    if is_admin_user(request.user):
        transfers = FileTransfer.objects.all().select_related('file','from_dept','to_dept','to_emp').order_by('-transferred_at')
    else:
        transfers = FileTransfer.objects.filter(Q(from_emp=emp) | Q(to_emp=emp)).select_related('file','from_dept','to_dept','to_emp').order_by('-transferred_at')
    return render(request, 'transfers/transfer_list.html', {'transfers': transfers, 'user': request.user, 'notif_count': get_notif_count(request.user), 'current_emp': emp})

@login_required(login_url='/login/')
def create_transfer(request):
    emp = get_emp(request.user)
    if is_admin_user(request.user):
        files = File.objects.filter(is_archived=False).select_related('current_department')
        depts = Department.objects.filter(active=True)
    else:
        files = File.objects.filter(is_archived=False, current_department=emp.department).select_related('current_department')
        depts = Department.objects.filter(active=True).exclude(id=emp.department.id)
    emps = Employee.objects.filter(active=True).exclude(id=emp.id).select_related('department')
    if request.method == 'POST':
        f = File.objects.get(id=request.POST['file_id'])
        td = Department.objects.get(id=request.POST['to_dept'])
        cnt = FileTransfer.objects.filter(transferred_at__date=timezone.now().date()).count()
        tn = f'TRF-{timezone.now().strftime("%Y%m%d")}-{str(cnt+1).zfill(4)}'
        to_emp_id = request.POST.get('to_emp') or None
        t = FileTransfer.objects.create(file=f, transfer_number=tn, from_dept=f.current_department, to_dept=td, from_emp=emp, to_emp_id=to_emp_id, transfer_type=request.POST.get('type','TRANSFER'), remarks=request.POST.get('remarks','').strip())
        f.current_department = td; f.status = 'TRANSFERRED'; f.save()
        FileMovement.objects.create(file=f, from_dept=t.from_dept, to_dept=td, action=f'Transferred to {td.name}', remarks=t.remarks, performed_by=emp)
        AuditLog.objects.create(user=request.user, payroll=request.user.payroll_number, action='TRANSFER_CREATED', module='Transfers', details={'transfer_number': tn})
        if to_emp_id:
            try:
                to_user = User.objects.get(employee_id=to_emp_id)
                Notification.objects.create(user=to_user, notification_type='FILE_TRANSFERRED', message=f'File {f.file_number}: "{f.subject}" sent to you by {emp.name}', file=f)
            except: pass
        else:
            dept_emps = Employee.objects.filter(department=td, active=True)
            for e in dept_emps:
                if hasattr(e, 'user') and e.user:
                    Notification.objects.create(user=e.user, notification_type='DEPT_FILE', message=f'File {f.file_number}: "{f.subject}" sent to {td.name} department', file=f)
        return redirect('/transfers/')
    return render(request, 'transfers/create_transfer.html', {'files': files, 'departments': depts, 'employees': emps, 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def api_dept_employees(request, dept_id):
    emps = Employee.objects.filter(department_id=dept_id, active=True).values('id', 'payroll', 'name')
    return JsonResponse(list(emps), safe=False)

@login_required(login_url='/login/')
def receive_transfer(request, pk):
    t = FileTransfer.objects.select_related('file','from_dept','to_dept').get(id=pk)
    if request.method == 'POST':
        report = request.POST.get('report', '').strip()
        hold_days = int(request.POST.get('hold_days', 7))
        t.status = 'RECEIVED'; t.received_at = timezone.now(); t.save()
        t.file.status = 'RECEIVED'
        emp = get_emp(request.user)
        t.file.current_holder = emp; t.file.date_received = timezone.now()
        t.file.hold_duration_days = hold_days
        t.file.expected_return_date = timezone.now() + timezone.timedelta(days=hold_days)
        t.file.save()
        FileMovement.objects.create(file=t.file, from_dept=t.from_dept, to_dept=t.to_dept, action='File Received', remarks=f'Received by {emp.name}. Expected return in {hold_days} days.', report=report if report else None, hold_days=hold_days, performed_by=emp)
        AuditLog.objects.create(user=request.user, payroll=request.user.payroll_number, action='TRANSFER_RECEIVED', module='Transfers', details={'transfer_number': t.transfer_number})
        if t.from_emp and hasattr(t.from_emp, 'user'):
            Notification.objects.create(user=t.from_emp.user, notification_type='FILE_RECEIVED', message=f'File {t.file.file_number} received by {emp.name}', file=t.file)
        return redirect('/transfers/')
    return render(request, 'transfers/receive_file.html', {'transfer': t, 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def return_file(request, pk):
    f = File.objects.get(id=pk)
    if request.method == 'POST':
        report = request.POST.get('report', '').strip()
        emp = get_emp(request.user)
        last_move = FileMovement.objects.filter(file=f).exclude(from_dept=None).first()
        return_dept = last_move.from_dept if last_move else f.department
        f.status = 'RETURNED'; f.current_department = return_dept; f.current_holder = None; f.save()
        FileMovement.objects.create(file=f, from_dept=emp.department, to_dept=return_dept, action='File Returned', remarks=f'Returned by {emp.name} after {f.days_held} days', report=report if report else None, performed_by=emp)
        dept_emps = Employee.objects.filter(department=return_dept, active=True)
        for e in dept_emps:
            if hasattr(e, 'user') and e.user:
                Notification.objects.create(user=e.user, notification_type='FILE_RETURNED', message=f'File {f.file_number}: "{f.subject}" returned by {emp.name}', file=f)
        return redirect(f'/file/{pk}/')
    return render(request, 'registry/return_file.html', {'file': f, 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def check_deadlines(request):
    today = timezone.now().date(); tomorrow = today + timezone.timedelta(days=1)
    due_tomorrow = File.objects.filter(expected_return_date__date=tomorrow, status__in=['RECEIVED','UNDER_REVIEW'], is_archived=False)
    for f in due_tomorrow:
        if f.current_holder and hasattr(f.current_holder,'user') and f.current_holder.user:
            Notification.objects.get_or_create(user=f.current_holder.user, file=f, notification_type='DEADLINE_WARNING', defaults={'message':f'File {f.file_number}: "{f.subject}" is due tomorrow!','is_read':False})
    overdue_files = File.objects.filter(expected_return_date__date__lt=today, status__in=['RECEIVED','UNDER_REVIEW'], is_archived=False)
    for f in overdue_files:
        if f.current_holder and hasattr(f.current_holder,'user') and f.current_holder.user:
            days_overdue = (today - f.expected_return_date.date()).days
            Notification.objects.get_or_create(user=f.current_holder.user, file=f, notification_type='FILE_OVERDUE', defaults={'message':f'OVERDUE! File {f.file_number} is {days_overdue} days past deadline!','is_read':False})
    return JsonResponse({'checked':True,'warnings':due_tomorrow.count(),'overdue':overdue_files.count()})

@login_required(login_url='/login/')
def notifications_list(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    return render(request, 'notifications.html', {'notifications': notifs, 'user': request.user, 'notif_count': 0})

@login_required(login_url='/login/')
def mark_notification_read(request, pk):
    Notification.objects.filter(id=pk, user=request.user).update(is_read=True)
    return redirect('/notifications/')

@login_required(login_url='/login/')
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('/notifications/')

@login_required(login_url='/login/')
def department_list(request):
    if not is_admin_user(request.user): return redirect('/')
    return render(request, 'departments/department_list.html', {'departments': Department.objects.all(), 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def add_department(request):
    if not is_admin_user(request.user): return redirect('/')
    if request.method == 'POST':
        Department.objects.create(code=request.POST['code'].strip().upper(), name=request.POST['name'].strip())
        return redirect('/departments/')
    return render(request, 'departments/department_form.html', {'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def employee_list(request):
    if not is_admin_user(request.user): return redirect('/')
    q = request.GET.get('q', '').strip()
    emps = Employee.objects.filter(active=True).select_related('department')
    if q: emps = emps.filter(Q(payroll__icontains=q) | Q(name__icontains=q) | Q(email__icontains=q))
    return render(request, 'departments/employee_list.html', {'employees': emps, 'q': q, 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def add_employee(request):
    if not is_admin_user(request.user): return redirect('/')
    if request.method == 'POST':
        Employee.objects.create(payroll=request.POST['payroll'].strip(), name=request.POST['name'].strip(), department_id=request.POST['dept'], email=request.POST['email'].strip(), designation=request.POST.get('designation','').strip(), phone=request.POST.get('phone','').strip())
        return redirect('/employees/')
    return render(request, 'departments/add_employee.html', {'departments': Department.objects.filter(active=True), 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def reports_dashboard(request):
    if not is_admin_user(request.user): return redirect('/')
    return render(request, 'reports/reports_dashboard.html', {'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def daily_report(request):
    if not is_admin_user(request.user): return redirect('/')
    date = request.GET.get('date', timezone.now().date().isoformat())
    files = File.objects.filter(created_at__date=date).select_related('current_department')
    return render(request, 'reports/daily_report.html', {'files': files, 'date': date, 'count': files.count(), 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def department_report(request):
    if not is_admin_user(request.user): return redirect('/')
    data = []
    for d in Department.objects.all():
        fs = File.objects.filter(current_department=d, is_archived=False)
        data.append({'name':d.name, 'total':fs.count(), 'completed':fs.filter(status='COMPLETED').count(), 'pending':fs.filter(status__in=['REGISTERED','RECEIVED','UNDER_REVIEW','PENDING_APPROVAL']).count(), 'overdue':fs.filter(expected_return_date__date__lt=timezone.now().date()).count()})
    return render(request, 'reports/department_report.html', {'data': data, 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def overdue_report(request):
    if not is_admin_user(request.user): return redirect('/')
    files = File.objects.filter(expected_return_date__date__lt=timezone.now().date(), is_archived=False).select_related('current_department','current_holder').order_by('expected_return_date')
    return render(request, 'reports/overdue_report.html', {'files': files, 'count': files.count(), 'user': request.user, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def profile(request):
    emp = get_emp(request.user)
    return render(request, 'accounts/profile.html', {'user': request.user, 'employee': emp, 'notif_count': get_notif_count(request.user)})

@login_required(login_url='/login/')
def change_password(request):
    error = ''
    if request.method == 'POST':
        u = request.user
        if u.check_password(request.POST['old_password']):
            if request.POST['new_password'] == request.POST['confirm_password']:
                if len(request.POST['new_password']) >= 8:
                    u.set_password(request.POST['new_password']); u.save()
                    logout(request)
                    return redirect('/login/')
                error = 'Password must be at least 8 characters'
            else: error = 'Passwords do not match'
        else: error = 'Current password is incorrect'
    return render(request, 'accounts/change_password.html', {'error': error, 'user': request.user, 'notif_count': get_notif_count(request.user)})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('password-reset/', password_reset, name='password_reset'),
    path('admin-reset-password/', admin_reset_password, name='admin_reset_password'),
    path('', home_redirect, name='home'),
    path('my-dashboard/', user_dashboard, name='my_dashboard'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('files/', file_list, name='files'),
    path('register/', register_file, name='register'),
    path('request-file/', request_file, name='request_file'),
    path('file/<int:pk>/', file_detail, name='file_detail'),
    path('file/<int:pk>/tracking/', file_tracking, name='tracking'),
    path('file/<int:pk>/upload/', upload_document, name='upload'),
    path('file/<int:pk>/download/<int:doc_id>/', download_document, name='download'),
    path('file/<int:pk>/delete/', delete_file, name='delete_file'),
    path('file/<int:pk>/return/', return_file, name='return_file'),
    path('transfers/', transfer_list, name='transfers'),
    path('transfers/create/', create_transfer, name='create_transfer'),
    path('transfers/<int:pk>/receive/', receive_transfer, name='receive_transfer'),
    path('api/dept-employees/<int:dept_id>/', api_dept_employees, name='api_dept_employees'),
    path('api/check-deadlines/', check_deadlines, name='check_deadlines'),
    path('departments/', department_list, name='departments'),
    path('departments/add/', add_department, name='add_department'),
    path('employees/', employee_list, name='employees'),
    path('employees/add/', add_employee, name='add_employee'),
    path('reports/', reports_dashboard, name='reports'),
    path('reports/daily/', daily_report, name='daily_report'),
    path('reports/department/', department_report, name='department_report'),
    path('reports/overdue/', overdue_report, name='overdue_report'),
    path('profile/', profile, name='profile'),
    path('change-password/', change_password, name='change_password'),
    path('notifications/', notifications_list, name='notifications'),
    path('notifications/<int:pk>/read/', mark_notification_read, name='mark_read'),
    path('notifications/mark-all-read/', mark_all_read, name='mark_all_read'),
]


