from django.contrib import admin
from django.contrib.admin import register
from .models import CustomUser, Project, Task, Feedback


# Register your models here.
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'added_by')
    search_fields = ('username', 'email')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'start_date', 'end_date', 'status', 'owner', 'budget')
    search_fields = ('title', 'owner__username')
    list_filter = ('status', 'start_date', 'end_date', 'owner')
    
    
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'due_date', 'status', 'priority', 'project')
    search_fields = ('title', 'project__title')
    list_filter = ('status', 'priority', 'project')
    
    
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'task','rating', 'date_submitted')
    search_fields = ('user__username', 'project__title')
    list_filter = ('rating', 'project','date_submitted' )    