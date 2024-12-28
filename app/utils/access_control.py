from functools import wraps
from flask import abort, current_app
from flask_login import current_user
from app.utils.subscription import check_feature_access

def feature_required(feature_name):
    """Decorator to check if user's school has access to a feature"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            if not check_feature_access(current_user.school, feature_name):
                abort(403)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def subscription_required(minimum_tier):
    """Decorator to check minimum subscription tier"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
                
            tiers = ['basic', 'standard', 'premium']
            current_tier = current_user.school.subscription_type
            
            if tiers.index(current_tier) < tiers.index(minimum_tier):
                abort(403)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator