from lib2to3.fixes.fix_input import context
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.template.context_processors import request
from django.db import transaction
from .models import CustomUser, Project, Task, Transaction, Feedback, ChatMessage
from .forms import ProjectForm, TaskForm, TransactionForm, FeedbackForm, Signin_User, CompanyCreationForm, CompanyUserCreationForm
from django.contrib.auth import authenticate, login, logout
from .utils import get_features, send_email
from .validators import validate_email, validate_password, validate_name, validate_phone_number, validate_age
from django.core.validators import EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .forms import Signin
from django.contrib import messages
from django.db.models import Count

from management.models import Project 
from django.views.decorators.cache import cache_control, never_cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q # For complex queries

import random
import string

# from .utils import get_features


###########--UserValidators---############
# validators.py

def validate_name(value):
    if not RegexValidator(r'^[a-zA-Z ]+$', 'Name must contain only letters and spaces.')(value):
        raise ValidationError('Name must contain only letters and spaces.')
    return value

def validate_email(value):
    EmailValidator('Enter a valid email address.')(value)
    if get_user_model().objects.filter(email=value).exists():
        raise ValidationError("This email is already in use.")
    return value

def validate_password(value):
    if not RegexValidator(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                          'Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one digit, and one special character.')(value):
        raise ValidationError('Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one digit, and one special character.')
    return value

def validate_confirm_password(password, confirm_password):
    if password != confirm_password:
        raise ValidationError("Passwords do not match.")
    return confirm_password

def validate_phone_number(value):
    if not RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')(value):
        raise ValidationError('Enter a valid phone number.')
    return value

def validate_amount(value):
    if not RegexValidator(r'^\d+(\.\d{1,2})?$', 'Enter a valid amount (e.g., 123.45).')(value):
        raise ValidationError('Enter a valid amount (e.g., 123.45).')
    return value

#################--UserViews---############


def signin_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = Signin(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']

            if role == 'Company_Head' or role == 'Company_Employee':
                messages.warning(request, "Company users cannot sign up directly. Please contact an admin.")
                return redirect('login')
            email= form.cleaned_data['email']
            if email:
                try:
                    existing_user = CustomUser.objects.get(email=email)
                    messages.error(request, "Email already exists. Please use a different email.")
                    return redirect('signup')
                except CustomUser.DoesNotExist:
                    pass
            user = form.save(commit=False)
            user.role = role
            user.set_password(form.cleaned_data['password1'])  
            user.save()

            raw_password = form.cleaned_data['password1']
            user = authenticate(request, username=user.username, password=raw_password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')

        else:
            print(form.errors) 
    else:
        form = Signin()

    return render(request, 'htmls/user/signup.html', {'form': form})




def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')  

        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.must_change_password:
                login(request, user)
                return redirect('force_password_change') 
            else:
                if user.is_superuser or user.role == 'Government':
                    login(request, user)
                    return redirect('admin_view')
                else:
                    login(request, user)
                    # Redirect to the dashboard or any other page
                    messages.success(request, 'Login successful.')
                    return redirect('dashboard')  
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'htmls/user/login.html')

    return render(request, 'htmls/user/login.html')


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

@login_required
def admin_dashboard(request):
    # Restrict access to Government role (adjust if System Admin is defined)
    # Check if the user is a superuser and has the 'Government' role
    if not request.user.is_superuser or request.user.role != 'Government':
        return redirect('login') # Redirect to dashboard if not authorized
    
    # Project status data for pie chart
    status_data = Project.objects.values('status').annotate(count=Count('id'))
    
    # Budget data for bar chart
    projects = Project.objects.filter(status__in=['Ongoing', 'Planning'])
    budget_data = [
        {
            'name': p.title,
            'allocated': float(p.budget),
            'used': float(Transaction.objects.filter(project=p).aggregate(Sum('amount'))['amount__sum'] or 0)
        } for p in projects
    ]
    
    # Task data for timeline (ordered by due date, limited to 10)
    task = Task.objects.all().order_by('due_date')[:10]
    task_data = [
        {
            'id': t.id,
            'title': t.title,
            'due_date': t.due_date.strftime('%Y-%m-%d'),
            'status': t.status,
            'priority': t.priority,
            'project': t.project.title
        } for t in task
    ]
    
    # User data (limited to 10)
    users = CustomUser.objects.all()[:10]
    user_data = [
        {
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'must_change_password': u.must_change_password
        } for u in users
    ]
    
    # Project data (limited to 10)
    project_data = [
        {
            'id': p.id,
            'title': p.title,
            'status': p.status,
            'budget': float(p.budget),
            'remaining_budget': float(p.get_remaining_budget()),
            'team_members': [member.username for member in p.team_members.all()],
            'start_date': p.start_date.strftime('%Y-%m-%d'),
        } for p in Project.objects.all()[:10]
    ]
    
    # Feedback summary
    feedback_summary = Feedback.objects.all().values('rating').annotate(
        count=Count('id')
    ).order_by('rating')
    
    # Transaction summary (total credit/debit)
    transaction_summary = Transaction.objects.values('transaction_type').annotate(total=Sum('amount'), count=Count('id'))
    
    context = {
        'features': get_features(request.user.role),
        'status_data': list(status_data),
        'budget_data': budget_data,
        'task_data': task_data,
        'user_data': user_data,
        'project_data': project_data,
        'feedback_summary': list(feedback_summary),
        'transaction_summary': list(transaction_summary)
    }
    return render(request, 'htmls/user/admin.html', context)


def change_password(request):
    if request.method == 'POST':
        mail = request.POST.get('email')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        try:
            user = get_user_model().objects.filter(email=mail).first()
            if user is None:
                raise get_user_model().DoesNotExist
        except get_user_model().DoesNotExist:
            messages.error(request, "No user found with this email.")
            return render(request, 'htmls/user/change_pass.html')

        if not user.check_password(old_password):
            messages.error(request, "Old password is incorrect.")
            return render(request, 'htmls/user/change_pass.html')
        
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'htmls/user/change_pass.html')

        # Update user password
        user.set_password(new_password)
        if hasattr(user, 'must_change_password'):
            user.must_change_password = False
        user.save()

        messages.add_message(request, messages.SUCCESS, 'Your password has been successfully reset.', extra_tags='password_reset')
        return redirect('login')  
    return render(request, 'htmls/user/change_pass.html')


@never_cache
@login_required
def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user = request.user
    features = get_features(user.role)
    context = {
        'features': features
    }

    return render(request, "htmls/user/newdash.html", context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout_view(request):
    logout(request)
    return redirect('login')  

from django.db.models import Count, Sum

@login_required
def chart_view(request):
    
    total_unread_dashboard_count = ChatMessage.objects.filter(
    receiver=request.user,
    is_read=False
    ).count()
    status_data = Project.objects.values('status').annotate(count=Count('id'))

    projects = Project.objects.filter(status__in=['Ongoing', 'Planning'])    
    bar_data = []
    for p in projects:
        bar_data.append({
            'name': p.title,
            'allocated':    float(p.budget),
            'used': float(Transaction.objects.filter(project=p).aggregate(Sum('amount'))['amount__sum'] or 0)
        })

    context = {
        'status_data': list(status_data),
        'budget_data': bar_data,
        'total_unread_dashboard_count': total_unread_dashboard_count,
        'message': request.GET.get('message', None)
    }
    return render(request, 'htmls/user/dashboard.html', context)



user = get_user_model()
@login_required 

def add_company(request):
    if request.method == 'POST':
        form = CompanyCreationForm(request.POST, added_by=request.user)
        if form.is_valid():
            user = form.save(commit=False)

            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            user.set_password(temp_password)
            user.force_password_change = True
            user.role = "Company_Head"
            user.added_by = request.user  # Set the user who added this company
            user.must_change_password = True  # Ensure the user must change password on first login
            user.save()

            subject = 'Your Company Account Login Credentials'
            message = f"Hello {user.username}, your password is {temp_password}"
            receipient_list = [user.email]

            try:
                send_email(subject, message, receipient_list)
                messages.success(request, "Email sent successfully.")
            except Exception as e:
                messages.error(request, f"Failed to send email: {e}")
                print(e)
            
            return redirect('change_password')
        else:
            messages.error(request, "Error adding company. Please check the form.")
    else:
        form = CompanyCreationForm(added_by=request.user)
    
    return render(request, 'htmls/user/adproject.html', {'form': form})


user = get_user_model()
@login_required 
def add_company_user(request):
    if request.method == 'POST':
        form = CompanyUserCreationForm(request.POST, added_by=request.user)
        if form.is_valid():
            user = form.save(commit=False)

            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            user.set_password(temp_password)
            user.force_password_change = True
            user.role = "Company_Employee"
            user.added_by = request.user  # Set the user who added this company
            user.must_change_password = True  # Ensure the user must change password on first login
            user.save()

            subject = 'Your Company Account Login Credentials'
            message = f"Hello {user.username}, your password is {temp_password}"
            receipient_list = [user.email]

            try:
                send_email(subject, message, receipient_list)
                messages.success(request, "Email sent successfully.")
            except Exception as e:
                messages.error(request, f"Failed to send email: {e}")
                print(e)
            
            return redirect('change_password')
        else:
            messages.error(request, "Error adding company. Please check the form.")
    else:
        form = CompanyCreationForm(added_by=request.user)
    
    return render(request, 'htmls/user/adproject.html', {'form': form})


#################--ProjectVIews---############
@login_required
def createproject(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES) 
        if form.is_valid():
            form.save()
            return redirect('ProjectList')  
        else:
            return render(request, 'htmls/project/create.html', {'form': form})  # Show form with errors
    else:
        form = ProjectForm()
        return render(request, 'htmls/project/create.html', {'form': form})

@   login_required
def projectlist(request):
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'all':
        data = Project.objects.all()

    else:
        data = Project.objects.filter(status=status_filter)

    return render(request, 'htmls/project/list.html', {'data': data})


def projectedit(request, id):
    data = get_object_or_404(Project, id=id)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=data, files=request.FILES) 
        if form.is_valid():
            form.save()
            data = Project.objects.get(id=id)
            return redirect('ProjectList')
        else:
            print(form.errors)
    else:
        form = ProjectForm(instance=data)
    context = {'form': form, 'data': data}
    return render(request, 'htmls/project/edit.html', context)

def projectdelete(request, id):
    data = get_object_or_404(Project, id=id)
    data.delete()
    return redirect('ProjectList')

@login_required
def projectview(request, id):
    data = Project.objects.get(id=id)
    return render(request, 'htmls/project/unique.html', {'data': data})

@login_required
def viewtask(request, project_id):
    try:
        # Convert the project_id string to an integer
        project_id = int(project_id)
        project = get_object_or_404(Project, id=project_id)
        tasks = Task.objects.filter(project=project) 

        context = {'project': project, 'tasks': tasks}
        return render(request, 'htmls/project/tasks.html', context)
    except ValueError:
        return render(request, 'error.html', {'message': 'Invalid project ID'})
    
def projectask(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    tasks = Task.objects.filter(project=project)  
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project  
            task.save()
            return redirect('View-Task', project_id=project_id) 
        else:
            print(form.errors)
            print(form.cleaned_data.get('assigned_to', [])) 
            return render(request, 'htmls/task/create.html', {'form': form, 'project': project })
    else:
        form = TaskForm(initial={'project': project , 'user': request.user})
        return render(request, 'htmls/task/create.html', {'form': form, 'project': project})
    
        
    
@login_required
def projectTransaction(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    remaining_budget = project.get_remaining_budget()
    transactions = Transaction.objects.filter(project=project)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.project = project
            transaction.user = request.user  
            transaction.save()
            return redirect('transaction_list', project_id=project_id)  
        else:
            return render(request, 'htmls/transaction/projectran.html', {'form': form, 'project': project, 'remaining_budget': remaining_budget})
    else:
        form = TransactionForm(initial={'project': project, 'user': request.user})
        return render(request, 'htmls/transaction/projectran.html', {'form': form, 'project': project, 'remaining_budget': remaining_budget})


#################--TaskViews---############
@login_required
def create_task(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)  # don't save to DB yet
            task.project = project          # assign the project
            task.save()                     # now save it
            return redirect('View-Task')     # change if needed to project-specific task list
        else:
            print(form.errors)
            return render(request, 'htmls/task/create.html', {'form': form})
    else:
        form = TaskForm()
        return render(request, 'htmls/task/create.html', {'form': form})



@login_required
def tasklist(request):
    status_filter = request.GET.get('status','all')
    if status_filter== 'all':
        data = Task.objects.all()

    else:
        data = Task.objects.filter(status=status_filter)
        
    return render(request, 'htmls/task/list.html', {'data':data})

@login_required
def taskview(request, id):
    data = Task.objects.get(id=id)
    return render(request, 'htmls/task/view.html', {'data':data})

def project_task(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    tasks = Task.objects.filter(project=project)  # Access all tasks associated with the project
    context = {'project': project, 'tasks': tasks}
    return render(request, 'htmls/project/tasks.html', context)

@login_required
def taskdelete(request, id):
    data = Task.objects.get(id=id)
    data.delete()
    return redirect('TaskList')
@login_required
def taskedit(request, id):
    data = get_object_or_404(Task, id=id)
    # form = TaskForm(instance=id)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=data)
        if form.is_valid():
            form.save()
            return redirect('TaskList')

        else:
            print(form.errors)


    else:
        form = TaskForm(instance=data)
    context = {'form':form, 'data':data}
    return render(request, 'htmls/task/edit.html', context)



# #################--TransactionViews---############
@login_required
def createtransaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, "Transaction created successfully!")
                return redirect('transaction_list', project_id=form.cleaned_data['project'].id)
                
            
            except Exception as e:
                print(e)
                
    else:
        form = TransactionForm()
        
    return render(request, 'htmls/transaction/create.html', {'form':form})  
                  
                
def edittransaction(request, id):
    with transaction.atomic():
        transaction_obj = Transaction.objects.select_for_update().get(id=id)
        if request.method == 'POST':
            form = TransactionForm(request.POST, instance=transaction_obj)
            if form.is_valid():
                form.save()
                return redirect('transaction_list', project_id=form.cleaned_data['project'].id)
            
        else:
            form = TransactionForm(instance=transaction_obj)
    return render(request, 'htmls/transaction/edit.html', {'form': form})

@login_required
def transaction_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    transactions = Transaction.objects.filter(project=project)
    remaining_balance = project.get_remaining_budget()
    response = render(request, 'htmls/transaction/projectlist.html', {
        'transactions': transactions,
        'project': project,
        'remaining_balance': remaining_balance
    })
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response

@login_required
def listtransaction(request):
    transactions = Transaction.objects.all()
    return render(request, 'htmls/transaction/list.html', {'transactions':transactions})

def deletetransaction(request,id):
    transaction = get_object_or_404(Transaction, id=id)
    project_id = transaction.project.id  
    transaction.delete()
    return HttpResponseRedirect(f'/projects/{project_id}/transactions/')

#################--FeedbackViews---############
@login_required
def contact(request):
    return render(request, 'htmls/feedback/contact.html')


@login_required
def submit_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            if request.user.is_authenticated:
                feedback.user = request.user
            feedback.save()

    else:
        form = FeedbackForm()

    return render(request, 'htmls/feedback/sendmail.html', {'form': form})
    
    
@login_required    
def about(request):
    number = Project.objects.filter(status='Completed').count()
    budget = Transaction.objects.filter(project__status='completed').aggregate(Sum('amount'))['amount__sum'] or 0    
    return render(request, 'htmls/feedback/about.html', {'number': number, 'budget': budget})




CustomUser = get_user_model()


from django.db.models import Count, Subquery, OuterRef, Value
from django.db.models.functions import Coalesce

CustomUser = get_user_model()

@login_required
def list_users_for_chat(request):
    current_user = request.user
    
    # Determine users the current_user can chat with based on roles
    # This logic should mirror your can_chat_with logic in the consumer
    eligible_roles_map = {
        'Company_Head': ['Company_Head', 'Company_Employee', 'Government', 'Public'], # Can chat with anyone
        'Company_Employee': ['Company_Head', 'Company_Employee'],
        'Government': ['Company_Head', 'Public', 'Government'], # Assuming Gov can chat with other Gov
        'Public': ['Government']
    }
    # Adjust the map above according to your exact business rules.
    # For 'Company_Head', if it's truly anyone, you might not need to filter by role, just exclude self.
    
    allowed_roles_for_chat = eligible_roles_map.get(current_user.role, [])
    
    if current_user.role == 'Company_Head': # Special case if they can chat with literally anyone
        users_to_chat_with_qs = CustomUser.objects.exclude(id=current_user.id)
    else:
        users_to_chat_with_qs = CustomUser.objects.filter(role__in=allowed_roles_for_chat).exclude(id=current_user.id)
    
    # Annotate with unread message count from each user in the queryset
    # Unread messages are sent by 'other_user' (sender=OuterRef('pk')) to 'current_user' (receiver=current_user)
    unread_subquery = ChatMessage.objects.filter(
        sender=OuterRef('pk'),
        receiver=current_user,
        is_read=False
    ).values('sender').annotate(count=Count('id')).values('count')

    users_annotated = users_to_chat_with_qs.annotate(
        unread_count=Coalesce(Subquery(unread_subquery[:1]), Value(0))
    ).order_by('-unread_count', 'username') # Show users with unread messages first

    context = {
        'users_to_chat_with': users_annotated,
        'current_user_role': current_user.get_role_display(),
        'current_user': current_user, # Pass current_user for JS if needed
    }
    return render(request, 'htmls/chats/list_users.html', context) # Ensure template path is correct



def _can_chat_with(user1, user2):
    """
    Helper function to determine if two users can chat.
    This should mirror the logic in your ChatConsumer.
    Consider moving this to a utils.py or a model method for DRYness.
    """
    if not user1 or not user2:
        return False
    if user1 == user2: # Cannot chat with oneself
        return False

    role1 = user1.role
    role2 = user2.role
    
    # Define chat permissions (adjust as per your exact rules)
    # Format: current_user_role: [list_of_roles_they_can_chat_with]
    permissions = {
        'Company_Head': ['Company_Head', 'Company_Employee', 'Government', 'Public'],
        'Company_Employee': ['Company_Head', 'Company_Employee'],
        'Government': ['Company_Head', 'Public', 'Government'], # Assuming Gov can chat with other Gov
        'Public': ['Government','Company_Head']
    }
    
    if role1 in permissions:
        return role2 in permissions[role1]
    return False


@login_required
def chat_room(request, other_username):
    current_user = request.user
    try:
        other_user = CustomUser.objects.get(username=other_username)
    except CustomUser.DoesNotExist:
        # Handle user not found, e.g., redirect to a list or show an error
        return redirect('list_users_for_chat') # Or some other appropriate page

    if current_user == other_user:
        # User trying to chat with themselves, redirect or show message
        return redirect('list_users_for_chat') # Or some other appropriate page

    # Check if these users are allowed to chat
    if not _can_chat_with(current_user, other_user):
        # You can redirect or show a specific "permission denied" page
        return HttpResponseForbidden("You are not allowed to chat with this user.")

    # Fetch previous messages between the two users
    # Messages where current_user is sender and other_user is receiver OR
    # Messages where other_user is sender and current_user is receiver
    chat_messages = ChatMessage.objects.filter(
        (Q(sender=current_user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=current_user))
    ).order_by('timestamp') # Order by timestamp to show in chronological order

    # Note: The ChatConsumer's connect method already handles marking messages
    # from other_user to current_user as read when the WebSocket connects.
    # So, we don't strictly need to do it here again. The consumer ensures
    # that when the user actively enters the chat (WS connects), messages are marked.

    context = {
        'other_user': other_user,
        'other_username_json': other_username, # For JS WebSocket URL
        'chat_messages': chat_messages,
        'current_user': current_user,
    }
    return render(request, 'htmls/chats/chat_room.html', context)