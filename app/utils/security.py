from functools import wraps
from flask import abort
from flask_login import current_user
import jwt
from datetime import datetime, timedelta
from app.config import Config

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def premium_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.school.has_premium_subscription():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def generate_confirmation_token(email):
    token = jwt.encode(
        {
            'email': email,
            'exp': datetime.utcnow() + timedelta(days=1)
        },
        Config.SECRET_KEY,
        algorithm='HS256'
    )
    return token

def confirm_token(token):
    try:
        data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        return data['email']
    except:
        return None