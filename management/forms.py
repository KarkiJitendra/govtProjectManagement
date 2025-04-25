from .models import Project
from django import forms
from .models import CustomUser, Task, Transaction, Feedback
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError



class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full border border-blue-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-blue-300 rounded px-3 py-2 h-24 focus:outline-none focus:ring focus:ring-blue-200'
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border border-blue-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-200'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full border border-blue-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-200'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full border border-blue-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-200'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full border border-blue-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-200'
            }),
            'project': forms.Select(attrs={
                'class': 'w-full border border-blue-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-200'
            }),
        }

# class ProjectForm(forms.ModelForm):
#     team_members= forms.ModelMultipleChoiceField(
#         queryset=CustomUser.objects.all(),
#         widget=forms.SelectMultiple,  # Or use forms.SelectMultiple for a dropdown
#         required=True
#     )
#     class Meta():
#         model = Project
#         fields = '__all__'

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'end_date': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400', 'type': 'date'}),
            'owner': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'budget': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'team_members': forms.SelectMultiple(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
        }

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
    
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email address is already in use. Please supply a different email address.")
        return email


class Signin_User(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Inform a valid email address.")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email address is already in use. Please supply a different email address.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
#################--userVIews---############
from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['user', 'project', 'amount', 'transaction_type', 'description']
        widgets = {
            'user': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'project': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'transaction_type': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300',
                'rows': 4,
                'placeholder': 'Enter transaction description...'
            }),
        }






class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['feedback_type', 'project', 'task', 'feedback_text', 'rating']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make project and task fields optional initially
        self.fields['project'].required = False
        self.fields['task'].required = False