from .models import Project
from django import forms
from .models import CustomUser, Task, Transaction, Feedback
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.utils import timezone
from management import validators
from django.core.exceptions import ValidationError


class BaseForm(forms.Form):
    def clean_name(self, value):
        if not RegexValidator(r'^[a-zA-Z ]+$', 'Enter a valid name (only letters and spaces).')(value):
            raise ValidationError('Enter a valid name (only letters and spaces).')
        return value

    # def clean_email(self, value):
    #     EmailValidator('Enter a valid email address.')(value)
    #     if CustomUser.objects.filter(email=value).exists():
    #         raise ValidationError("This email is already in use.")
    #     return value

    def clean_password(self, value):
        if not RegexValidator(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                              'Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one digit, and one special character.')(value):
            raise ValidationError('Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one digit, and one special character.')
        return value

    def clean_phone_number(self, value):
        if not RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')(value):
            raise ValidationError('Enter a valid phone number.')
        return value

    def clean_age(self, value):
        if not (0 < value < 120):
            raise ValidationError('Age must be between 1 and 119.')
        return value

class TaskForm(forms.ModelForm, BaseForm):
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
            'assigned_to': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2 px-2 py-1 bg-blue-50 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400'
            }),
            'project': forms.Select(attrs={
                'class': 'w-full border border-blue-300 rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-200'
            }),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(status__in=['Planning','Ongoing'])
        # Filter assigned_to field to only show Company_Employee users
        self.fields['assigned_to'].queryset = CustomUser.objects.filter(role='Company_Employee')

        
    def clean_title(self):
        title = self.cleaned_data['title']
        if not title.strip():
            raise forms.ValidationError('Title cannot be empty.')
        return title
    
    def clean_description(self):
        description = self.cleaned_data['description']
        if not description.strip():
            raise forms.ValidationError('Description cannot be empty.')
        return description
    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now().date():
            raise forms.ValidationError('Due date cannot be in the past.')
        return due_date
    def clean_priority(self):
        priority = self.cleaned_data['priority']
        if priority not in ['Low', 'Medium', 'High']:
            raise forms.ValidationError('Invalid priority level.')
        return priority

    
    def clean_status(self):
        status = self.cleaned_data['status']
        if status not in ['Pending', 'In Progress', 'Completed']:
            raise forms.ValidationError('Invalid status.')
        return status



class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ['start_date', 'project']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'end_date': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400', 'type': 'date'}),
            'owner': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'budget': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'team_members': forms.CheckboxSelectMultiple(attrs={'class': 'space-y-2 px-2 py-1 bg-blue-50 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full px-4 py-2 border border-blue-300 rounded-md bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter owner field to only show Company_head users
        self.fields['owner'].queryset = CustomUser.objects.filter(role='Company_Head')

        # If 'owner' is in the data (form submission), use it to filter team_members
        # if 'owner' in self.data:
        #     try:
        #         owner_id = int(self.data.get('owner'))
        #         self.fields['team_members'].queryset = CustomUser.objects.filter(role='Company_Employee', added_by_id=owner_id)
        #     except (ValueError, TypeError):
        #         self.fields['team_members'].queryset = CustomUser.objects.none()
        # elif self.instance.pk:
        #     # In case of editing existing object
        #     owner = self.instance.owner
        self.fields['team_members'].queryset = CustomUser.objects.filter(role='Company_Employee')
       

    def clean_title(self):
        title = self.cleaned_data['title']
        if not title.strip():
            raise forms.ValidationError('Title cannot be empty.')
        return title

    def clean_description(self):
        description = self.cleaned_data['description']
        if not description.strip():
            raise forms.ValidationError('Description cannot be empty.')
        return description

    def clean_budget(self):
        budget = self.cleaned_data['budget']
        if budget <= 0:
            raise forms.ValidationError('Budget must be greater than zero.')
        return budget

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')

        # Use the instance's start_date or current date if new
        start_date = self.instance.start_date if self.instance.pk else timezone.now().date()

        if start_date is None:
            raise ValidationError('Start date must be set before setting the end date.')

        if end_date and end_date < start_date:
            raise ValidationError('End date must be after the start date.')

        return end_date


class Signin(forms.ModelForm, BaseForm):
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
        
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in password1):
            raise forms.ValidationError("Password must contain at least one digit")
        if not any(char.isalpha() for char in password1):
            raise forms.ValidationError("Password must contain at least one letter")
        if not any(char in "!@#$%^&*()_+" for char in password1):
            raise forms.ValidationError("Password must contain at least one special character")
        return password1

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


class Signin_User(UserCreationForm, forms.ModelForm, BaseForm):
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
    
    



from django import forms
from .models import CustomUser

class CompanyCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300'
            }),
        }


    def __init__(self, *args, **kwargs):
        self.added_by = kwargs.pop('added_by', None)  # <- Accept from view
        super().__init__(*args, **kwargs)

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
            
            
class CompanyUserCreationForm(forms.ModelForm, BaseForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email']  # Only required fields


    def __init__(self, *args, **kwargs):
        self.added_by = kwargs.pop('added_by', None)  # <- Accept from view
        super().__init__(*args, **kwargs) 
            
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

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        exclude = ['user']  # user will be assigned in the view, not through the form
        widgets = {
            'project': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'transaction_type': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300'}),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring focus:border-blue-300',
                'rows': 4,
                'placeholder': 'Enter transaction description...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('transaction_type')
        amount = cleaned_data.get('amount')

        if transaction_type not in ['Credit', 'Debit']:
            self.add_error('transaction_type', "Invalid transaction type.")

        if amount is not None and amount <= 0:
            self.add_error('amount', f"{transaction_type} transactions must have a positive amount.")

        return cleaned_data


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['feedback_type', 'project', 'task', 'feedback_text', 'rating']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make project and task fields optional initially
        self.fields['project'].required = False
        self.fields['task'].required = False