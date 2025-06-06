from django.urls import path
from .views import login_view, signin_view, dashboard_view, createproject, projectlist, projectedit, projectdelete, \
    projectview, create_task, tasklist, taskview, taskedit, taskdelete, viewtask, transaction_list, createtransaction,\
    edittransaction, deletetransaction, listtransaction, submit_feedback, contact, add_company, logout_view, change_password, projectTransaction, about, chart_view, add_company_user, projectask, admin_dashboard, list_users_for_chat, chat_room

urlpatterns = [
    path('login/', login_view, name='login'),
    path('', signin_view, name='signup'),
    # path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    path('projectuser/',add_company, name='add_company'), 
    path('projectemployee/',add_company_user, name='add_company_user'), 
    # path('dashboard/', pie_chart_view, name='dashboard'),
    path('change_password/', change_password, name='change_password'),
    path('dashboard/', chart_view, name='dashboard'),
    path('useradmin/', admin_dashboard, name='admin_view'),
    
    #project urls
    path('project/', createproject, name='create_project'),
    path('project/list/', projectlist, name='ProjectList'),
    path('project/edit/<id>', projectedit, name='Project-Edit'),
    path('project/delete/<id>', projectdelete, name='Project-Delete'),
    path('project/view/<id>', projectview, name='Project-View'),
    path('project/view/task/<int:project_id>/', viewtask, name='View-Task'),
    path('project/view/transaction /<int:project_id>/', projectTransaction, name='project-transaction'),
    path('project/create/task/<int:project_id>/', projectask, name='project-task'),
    

    #task urls
    path('task/<int:project_id>/', create_task, name='Create_Task'),
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
    
    
    path('contact/feedback/', submit_feedback, name='thank-you'),
    path('contact/', contact, name='contactpage'),
    path('about/', about, name='about'),
    
    path('chat/users/', list_users_for_chat, name='list_users_for_chat'),
    path('chat/with/<str:other_username>/', chat_room, name='chat_room'),
    
    
    
    
]