from django.urls import path
from .views import login_view, signin_view, dashboard_view, createproject, projectlist, projectedit, projectdelete, \
    projectview, create_task, tasklist, taskview, taskedit, taskdelete, viewtask, transaction_list, createtransaction,\
    edittransaction, deletetransaction, listtransaction, submit_feedback

urlpatterns = [
    path('login/', login_view, name='login'),
    path('', signin_view, name='signup'),
    path('dashboard/', dashboard_view, name='dashboard'),

    #project urls
    path('project/', createproject, name='create_project'),
    path('project/list/', projectlist, name='ProjectList'),
    path('project/edit/<id>', projectedit, name='Project-Edit'),
    path('project/delete/<id>', projectdelete, name='Project-Delete'),
    path('project/view/<id>', projectview, name='Project-View'),
    path('project/view/task/<int:project_id>/', viewtask, name='View-Task'),

    #task urls
    path('task/', create_task, name='Create_Task'),
    path('task/list/', tasklist, name='TaskList'),
    path('task/view/<id>', taskview, name='TaskView'),
    path('task/edit/<id>', taskedit, name='Task-Edit'),
    path('task/delete/<id>', taskdelete, name='Task-Delete'),

    # transaction urls
    path('projects/<int:project_id>/transactions/', transaction_list, name='transaction_list'),
    path('transactions/list', listtransaction, name='list_transaction'),
    path('transactions/', createtransaction, name='create_transaction'),
    path('transactions/edit/<int:id>/', edittransaction, name='edit_transaction'),
    path('transactions/delete/<int:id>/', deletetransaction, name='delete_transaction'),
    
    
    path('feedback/', submit_feedback, name='thank-you'),
    
    
    
]