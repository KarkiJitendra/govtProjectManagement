# validators.py
from django.core.validators import EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

def validate_name(value):
    if not RegexValidator(r'^[a-zA-Z ]+$', 'Enter a valid name (only letters and spaces).')(value):
        raise ValidationError('Enter a valid name (only letters and spaces).')
    return value

def validate_email(value):
    EmailValidator('Enter a valid email address.')(value)
    if User.objects.filter(email=value).exists():
        raise ValidationError("This email is already in use.")
    return value

def validate_password(value):
    if not RegexValidator(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                          'Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one digit, and one special character.')(value):
        raise ValidationError('Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one digit, and one special character.')
    return value

def validate_phone_number(value):
    if not RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')(value):
        raise ValidationError('Enter a valid phone number.')
    return value

def validate_age(value):
    if not (0 < value < 120):
        raise ValidationError('Age must be between 1 and 119.')
    return value