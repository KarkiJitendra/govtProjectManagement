# utils.py
import os
from mailjet_rest import Client
from django.conf import settings


def send_email(subject, text_part, html_part, recipient_email, recipient_name):
    # api_key = os.getenv('MJ_APIKEY_PUBLIC')
    # api_secret = os.getenv('MJ_APIKEY_PRIVATE')
    # mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    mailjet = Client(auth=(settings.MJ_APIKEY_PUBLIC, settings.MJ_APIKEY_PRIVATE), version='v3.1')

    data = {
        'Messages': [
            {
                'From': {
                    'Email': 'sabrejiten9761@gmail.com',
                    'Name': 'Jitendra Karki',
                },
                'To': [
                    {
                        'Email': recipient_email,
                        'Name': recipient_name,
                    }
                ],
                'Subject': subject,
                'TextPart': text_part,
                'HtmlPart': html_part,
            }
        ]
    }

    try:
        result = mailjet.send.create(data=data)
        print("Mailjet API Response:", result.status_code)
        print("Mailjet API Response Body:", result.json())

        # Optional: Check for 200 status code or errors in the body
        if result.status_code != 200:
            raise Exception("Mailjet failed to send email.")
        return result
    except Exception as e:
        print("Mailjet API Error:", e)
        raise e


from .models import CustomUser
def get_features(role):
    role_features = {
        'Government': ['project_mgmt', 'audit_report'],
        'Company': ['task_mgmt', 'Manage Employees','risk_analysis','transaction'],
        'Public': ['Access Public Services', 'Submit Feedback']
    }
    return role_features.get(role, [])