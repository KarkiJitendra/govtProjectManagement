from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings

class CustomUser(AbstractUser):
        ROLE_CHOICES = [
            ('Government', 'Government'),
            ('Company_Head', 'Company_Head'),
            ('Company_Employee', 'Company_Employee'),
            ('Public', 'Public'),
        ]
        role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Public')
        must_change_password = models.BooleanField(default=False)


class Project(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=50, choices=[('Planning', 'Planning'), ('Ongoing', 'Ongoing'), ('Completed', 'Completed')])
    start_date = models.DateField(auto_now_add=True)  # Set start_date to creation time
    end_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(CustomUser, related_name='projects', on_delete=models.CASCADE)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    # tasks = models.ManyToManyField('Task', related_name='projects', blank=True, null=True)
    # Rename related_tasks to something else
    # related_tasks_field = models.CharField(max_length=255, blank=True, null=True)
    team_members = models.ManyToManyField(CustomUser, related_name='assigned_projects')
    image = models.ImageField(upload_to='project_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.title}, {self.status}, {self.start_date}"
    
    def get_remaining_budget(self):
        total_spent = self.transaction_set.aggregate(total=models.Sum('amount'))['total'] or 0
        return self.budget - total_spent
    
    
    

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField()
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('In Progress', 'In Progress'),
                                                      ('Completed', 'Completed')])
    assigned_to = models.ForeignKey(CustomUser, related_name='tasks', on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='tasks_for_project')
    priority = models.CharField(max_length=50, choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')])

class Transaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)  # Optional
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=50, choices=[('Credit', 'Credit'), ('Debit', 'Debit')])
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    
    
    def clean(self):
        # Example: Ensure amount is positive for credit transactions
        if self.transaction_type == 'Credit' and self.amount <= 0:
            raise ValidationError("Credit transactions must have a positive amount.")
        
    def get_remaining_budget(self):
        total_spent = self.transaction_set.aggregate(total=models.Sum('amount'))['total'] or 0
        return self.budget - total_spent
        
    def save(self, *args, **kwargs):
        self.clean()  # Perform validation
        if  self.project:
            # Update the project's budget
            remaining_budget = self.project.get_remaining_budget()
            if self.amount > remaining_budget:
                raise ValidationError("Insufficient budget.")
        super().save(*args, **kwargs)




class Feedback(models.Model):
    FEEDBACK_TYPE_CHOICES = [
        ('project', 'Project'),
        ('task', 'Task'),
        ('webpage', 'Webpage'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    feedback_type = models.CharField(max_length=10, choices=FEEDBACK_TYPE_CHOICES, default='webpage')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    feedback_text = models.TextField()
    rating = models.IntegerField(choices=[(1, 'Poor'), (2, 'Fair'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')], null=True, blank=True)
    date_submitted = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Ensure feedback is linked to the correct type
        if self.feedback_type == 'project' and not self.project:
            raise ValidationError("Project feedback must be linked to a project.")
        if self.feedback_type == 'task' and not self.task:
            raise ValidationError("Task feedback must be linked to a task.")
        if self.feedback_type == 'webpage' and (self.project or self.task):
            raise ValidationError("Webpage feedback cannot be linked to a project or task.")
        
        
        # Run validation before saving
        self.full_clean()
        super().save(*args, **kwargs)

        # Send email notification
        subject = f"New Feedback Submitted by {self.user.username}"
        message = (
                f"Feedback Details:\n\n"
                f"User: {self.user.username}\n"
                f"Project: {self.project.title if self.project else 'N/A'}\n"
                f"Task: {self.task.title if self.task else 'N/A'}\n"
                f"Rating: {self.get_rating_display()}\n"
                f"Feedback: {self.feedback_text}\n"
                f"Date: {self.date_submitted}"
            )
        send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['your@gmail.com'],  # Your Gmail address
                fail_silently=False,
            )

    def __str__(self):
        return f"Feedback on {self.get_feedback_type_display()} by {self.user or 'Anonymous'}"