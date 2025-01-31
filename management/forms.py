from .models import Project
from django import forms
from .models import CustomUser, Task, Transaction, Feedback

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'status', 'assigned_to', 'project', 'priority']

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = CustomUser.objects.all()
        self.fields['project'].queryset = Project.objects.all()

class ProjectForm(forms.ModelForm):
    team_members= forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.SelectMultiple,  # Or use forms.SelectMultiple for a dropdown
        required=True
    )
    class Meta():
        model = Project
        fields = '__all__'

class Signin(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    #     email = forms.EmailField(required=True)
    ROLE_CHOICES = [
        ('Government', 'Government'),
        ('Company', 'Company'),
        ('Public', 'Public'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'role']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return password2


#################--userVIews---############
class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = '__all__'
