# utils.py
import os
# from mailjet_rest import Client
from django.conf import settings
from django.core.mail import send_mail
from .models import CustomUser
def get_features(role):
    role_features = {
        'Government': ['project_mgmt', 'audit_report'],
        'Company': ['task_mgmt', 'Manage Employees','risk_analysis','transaction'],
        'Public': ['Access Public Services', 'Submit Feedback']
    }
    return role_features.get(role, [])

def send_email(subject, message, recipient_list):
    from_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, from_email, recipient_list)