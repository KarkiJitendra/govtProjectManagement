from .models import CustomUser
def get_features(role):
    role_features = {
        'Government': ['project_mgmt', 'audit_report'],
        'Company': ['task_mgmt', 'Manage Employees','risk_analysis','transaction'],
        'Public': ['Access Public Services', 'Submit Feedback']
    }
    return role_features.get(role, [])