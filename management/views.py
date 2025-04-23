from lib2to3.fixes.fix_input import context

from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.template.context_processors import request
from django.db import transaction

from .models import Project, Task, Transaction
from .forms import ProjectForm, TaskForm, TransactionForm, FeedbackForm, Signin_User
from django.contrib.auth import authenticate, login, logout
from .utils import get_features
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
#################--userVIews---############

from .forms import Signin
from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from .utils import get_features



def signin_view(request):
    if request.method == 'POST':
        form = Signin(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']

            # Prevent signup for role 'Company'
            if role == 'Company':
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
            login(request, user)

            # Handle next parameter for redirection
            # next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            # return redirect(next_url)
            return redirect('dashboard')
        else:
            # Add error message for invalid credentials
            messages.error(request, 'Invalid username or password.')
            return render(request, 'htmls/user/login.html')

    # Render login form for GET request
    return render(request, 'htmls/user/login.html')

def logout_view(request):
    # Handle user logout
    logout(request)
    return redirect('login')  # Redirect to login page after logout


def dashboard_view(request):
    user = request.user
    features = get_features(user.role)
    context = {
        'features': features
    }

    return render(request, "htmls/user/dashboard.html", context)




def add_company(request):
    if request.method == 'POST':
        form = Signin(request.POST)
        if form.is_valid():
            # Create a new user instance but avoid saving it yet
            user = form.save(commit=False)
            # Set the password
            user.password = make_password(form.cleaned_data['password1'])
            # Save the user to the database
            user.save()
            messages.success(request, "User added successfully!")
            return redirect('dashboard')  # Redirect to a success page or dashboard
        else:
            messages.error(request, "Error adding user. Please check the form.")
    else:
        form = Signin()
    return render(request, 'htmls/user/adproject.html', {'form': form})
    

# def add_company(request):
#     if request.method == 'POST':
#         form = Signin_User(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.role = 'Company'
#             user.set_password(form.cleaned_data['password1'])
#             user.save()
#             messages.success(request, "Company added successfully!")
#             return redirect('dashboard')  # Redirect to a success page or dashboard
#         else:
#             messages.error(request, "Error adding company. Please check the form.")
#             print(form.errors)  # Print form errors to the console
#     else:
#         form = Signin_User()
#     return render(request, 'htmls/user/addproject.html', {'form': form})

#################--ProjectVIews---############
def createproject(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ProjectList')  # Redirect to a list or details page after successful creation
        else:
            return render(request, 'htmls/project/create.html', {'form': form})  # Show form with errors
    else:
        form = ProjectForm()
        return render(request, 'htmls/project/create.html', {'form': form})


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
        form = ProjectForm(request.POST, instance=data)
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


def projectview(request, id):
    data = Project.objects.get(id=id)
    return render(request, 'htmls/project/unique.html', {'data': data})

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

def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect ('TaskList')

        else:
            print(form.errors)
            return render(request,'htmls/task/create.html', {'form':form})

    else:
        form = TaskForm()
        return  render(request,'htmls/task/create.html', {'form':form})



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


def taskview(request, id):
    data = Task.objects.get(id=id)
    return render(request, 'htmls/task/view.html', {'data':data})

def taskdelete(request, id):
    data = Task.objects.get(id=id)
    data.delete()
    return redirect('TaskList')

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