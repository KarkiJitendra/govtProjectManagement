from lib2to3.fixes.fix_input import context

from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.template.context_processors import request
from django.db import transaction

from .models import Project, Task, Transaction
from .forms import ProjectForm, TaskForm, TransactionForm
from django.contrib.auth import authenticate, login
from .utils import get_features

#################--userVIews---############

from .forms import Signin
from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from .utils import get_features



def signin_view(request):
    if request.method == 'POST':
        form = Signin(request.POST)
        if form.is_valid():
            # Save the user
            user = form.save(commit=False)
            user.role = form.cleaned_data['role']
            user.set_password(form.cleaned_data['password1'])  # Hash the password
            user.save()

            # Authenticate and log in the user
            raw_password = form.cleaned_data['password1']
            user = authenticate(request, username=user.username, password=raw_password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # Use redirect instead of render

        else:
            print(form.errors)  # Debug: Check validation errors
            return render(request, 'htmls/user/signup.html', {'form': form})
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


def dashboard_view(request):
    user = request.user
    features = get_features(user.role)
    context = {
        'features': features
    }

    return render(request, "htmls/user/dashboard.html", context)


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
        data = Task.objects.get(status=status_filter)

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
                return redirect('list_transaction')
            
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











