from lib2to3.fixes.fix_input import context
import json
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.template.context_processors import request
from django.db import transaction

from .models import Project, Task, Transaction
from .forms import ProjectForm, TaskForm, TransactionForm, FeedbackForm, Signin_User, CompanyCreationForm, CompanyUserCreationForm
from django.contrib.auth import authenticate, login, logout
from .utils import get_features
from .validators import validate_email, validate_password, validate_name, validate_phone_number, validate_age
from django.core.validators import EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
#################--userVIews---############
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

            # Prevent signup for role 'Company'
            if role == 'Company_Head' or role == 'Company_Employee':
                # You can add a message if you use messages framework
                messages.warning(request, "Company users cannot sign up directly. Please contact an admin.")
                return redirect('login')
        
            user = form.save(commit=False)
            user.role = role
            user.set_password(form.cleaned_data['password1'])  # Hash the password
            user.save()

            # Authenticate and log in the user
            raw_password = form.cleaned_data['password1']
            user = authenticate(request, username=user.username, password=raw_password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')

        else:
            print(form.errors)  # Debug: Check validation errors

    else:
        form = Signin()

    return render(request, 'htmls/user/signup.html', {'form': form})




def login_view(request):
    if request.method == 'POST':
        # Retrieve username and password from POST data
        username = request.POST.get('username')
        password = request.POST.get('password')  # Ensure field name matches your form

        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.must_change_password:
                login(request, user)
                return redirect('force_password_change')  # name of the view to force password change
            else:
                login(request, user)
                return redirect('dashboard')  # or role-based dashboard
        else:
            # Add error message for invalid credentials
            messages.error(request, 'Invalid username or password.')
            return render(request, 'htmls/user/login.html')

    # Render login form for GET request
    return render(request, 'htmls/user/login.html')


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)


def change_password(request):
    if request.method == 'POST':
        mail = request.POST.get('email')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Validate email


        # Validate new password
        try:
            new_password = validate_password(new_password)
        except ValidationError as e:
            messages.error(request, e.message)
            return render(request, 'htmls/user/change_pass.html')

        # Check if passwords match
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'htmls/user/change_pass.html')

        # Check if user exists
        try:
            user = get_user_model().objects.get(email=mail)
        except ObjectDoesNotExist:
            messages.error(request, "No user found with this email.")
            return render(request, 'htmls/user/change_pass.html')

        # Update user password
        user.set_password(new_password)
        if hasattr(user, 'must_change_password'):
            user.must_change_password = False
        user.save()

        messages.add_message(request, messages.SUCCESS, 'Your password has been successfully reset.', extra_tags='password_reset')
        return redirect('login')  # Redirect to login after reset

    return render(request, 'htmls/user/change_pass.html')
# def forgotten_password(request):
    
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         password = request.POST.get('password')

#         try:
#             validate_email(email)
#             validate_password(password)
#         except ValidationError as e:
#             return render(request, 'forgotten_password.html', {'error': e.message})

#         try:
#             user = get_user_model().objects.filter(email=email)
#         except ObjectDoesNotExist:
#             messages.error(request, "No user found with this email.")
#             return render(request, 'htmls/user/change_pass.html')

#         user.set_password(password)
#         user.save()

#         send_mail(
#             subject='Your Company Account Password Reset',
#             message=f"Dear {user.username},\n\nYour password has been reset.\nNew password: {password}\nPlease log in and change your password immediately.",
#             from_email=settings.EMAIL_HOST_USER,
#             recipient_list=[email],
#             fail_silently=False,
#         )

#         return redirect('login')
#     else:
#         return render(request, 'htmls/user/change_pass.html')



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
    # Handle user logout
    logout(request)
    return redirect('login')  # Redirect to login page after logout

@login_required
def pie_chart_view(request):
    plan = Project.objects.filter(status='Planning').count()
    ongoing = Project.objects.filter(status='Ongoing').count()
    completed = Project.objects.filter(status='Completed').count()

    labels = ["Planning", "Ongoing", "Completed"]
    data = [plan, ongoing, completed]

    context = {
        'labels': json.dumps(labels),
        'data': json.dumps(data),
    }
    return render(request, 'htmls/user/dashboard.html', context)


user = get_user_model()

@login_required
# views.py


# def generate_temp_password(length=10):
#     return ''.join(random.choices(string.ascii_letters + string.digits, k=length))  # Default length is 10

def add_company(request):
    if request.method == 'POST':
        form = CompanyCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Generate and set temporary password
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))  # Default length is 10
            user.set_password(temp_password)

            # Mark as requiring password change
            user.force_password_change = True
            user.role = "Company_Head"  # Ensure role is set to Company
            user.save()

            # Send email with the temp password
            send_mail(
                subject='Your Company Account Login Credentials',
                message=f"Dear {user.username},\n\nYour account has been created.\nTemporary password: {temp_password}\nPlease log in and change your password immediately.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(request, "Company admin added and email sent successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Error adding company. Please check the form.")
    else:
        form = CompanyCreationForm()
    
    return render(request, 'htmls/user/adproject.html', {'form': form})


    

#################--ProjectVIews---############
@login_required
def createproject(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)  # Include request.FILES for file uploads
        if form.is_valid():
            form.save()
            return redirect('ProjectList')  # Redirect to a list or details page after successful creation
        else:
            return render(request, 'htmls/project/create.html', {'form': form})  # Show form with errors
    else:
        form = ProjectForm()
        return render(request, 'htmls/project/create.html', {'form': form})

@   login_required
def projectlist(request):
    # data = Project.objects.all()
    # context = {'data':data}
    # return render(request, 'list.html', context)

    status_filter = request.GET.get('status', 'all')
    if status_filter == 'all':
        data = Project.objects.all()

    else:
        data = Project.objects.filter(status=status_filter)

    return render(request, 'htmls/project/list.html', {'data': data})


def projectedit(request, id):
    data = get_object_or_404(Project, id=id)
    # form = ProjectForm(instance=data)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=data, files=request.FILES)  # Include request.FILES for file uploads
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
        tasks = Task.objects.filter(project=project)  # Access all tasks associated with the project

        context = {'project': project, 'tasks': tasks}
        return render(request, 'htmls/project/tasks.html', context)
    except ValueError:
        # Handle the case where project_id cannot be converted to an integer
        return render(request, 'error.html', {'message': 'Invalid project ID'})



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
            return redirect('TaskList')     # change if needed to project-specific task list
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
    # status_filter = request.GET.get('status', 'all')  # Get the category from the request
    # if status_filter:
    #     tasks = Task.objects.filter(status=status_filter)  
    # else:
    #     tasks = Task.objects.all()
        
    return render(request, 'htmls/task/list.html', {'data':data})

@login_required
def taskview(request, id):
    data = Task.objects.get(id=id)
    return render(request, 'htmls/task/view.html', {'data':data})
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



#################--TransactionViews---############
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
    #to make the transaction atomic i.e no roll back issue
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response

@login_required
def listtransaction(request):
    transactions = Transaction.objects.all()
    return render(request, 'htmls/transaction/list.html', {'transactions':transactions})

def deletetransaction(request,id):
    transaction = get_object_or_404(Transaction, id=id)
    project_id = transaction.project.id  # Save the project ID before deleting the transaction
    transaction.delete()
    return HttpResponseRedirect(f'/projects/{project_id}/transactions/')

    # Redirect back to the project's transaction list page

#################--FeedbackViews---############


def submit_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            if request.user.is_authenticated:
                feedback.user = request.user
            feedback.save()

            # # Send email notification
            # subject = f"New Feedback on {feedback.get_feedback_type_display()}"
            # message = (
            #     f"Feedback Details:\n\n"
            #     f"User: {feedback.user or 'Anonymous'}\n"
            #     f"Type: {feedback.get_feedback_type_display()}\n"
            #     f"Project: {feedback.project.title if feedback.project else 'N/A'}\n"
            #     f"Task: {feedback.task.title if feedback.task else 'N/A'}\n"
            #     f"Rating: {feedback.get_rating_display() if feedback.rating else 'N/A'}\n"
            #     f"Feedback: {feedback.feedback_text}\n"
            #     f"Date: {feedback.date_submitted}"
            # )
            # try:
            #     send_mail(
            #         subject=subject,
            #         message=message,
            #         from_email=settings.EMAIL_HOST_USER,
            #         recipient_list=['jitendrakarki988036@gmail.com'],  # Change this to the recipient's email"],
            #         fail_silently=False,
            #     )
            #     return JsonResponse({'status': 'success', 'message': 'Email sent successfully!'})
            # except Exception as e:
            #     return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        form = FeedbackForm()

    return render(request, 'htmls/feedback/sendmail.html', {'form': form})

   


    #         return render(request, 'htmls/feedback/thanku.html')  # Redirect to a thank-you page
    # else:
    #     form = FeedbackForm()
    # return render(request, 'htmls/feedback/contact.html', {'form': form})