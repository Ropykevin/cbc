from typing import Optional
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash
import jwt
from app.extensions import db
from app.models.user import User
from app.models.school import School
from app.services.email_service import EmailService

class AuthService:
    @staticmethod
    def register_user(data: dict) -> User:
        """Register a new user and school"""
        try:
            # Create school
            school = School(
                name=data['school_name'],
                email=data['email'],
                subscription_type=data.get('subscription_type', 'basic')
            )
            db.session.add(school)
            db.session.flush()  # Get school.id without committing

            # Create admin user
            user = User(
                username=data['admin_name'],
                email=data['email'],
                password_hash=generate_password_hash(data['password']),
                role='admin',
                school_id=school.id,
                email_verified=False
            )
            db.session.add(user)
            db.session.commit()

            # Send verification email
            AuthService.send_verification_email(user)
            return user

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            raise

    @staticmethod
    def verify_email(token: str) -> bool:
        """Verify user's email address"""
        try:
            data = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            user = User.query.get(data['user_id'])
            if user:
                user.email_verified = True
                db.session.commit()
                return True
        except Exception as e:
            current_app.logger.error(f"Email verification error: {str(e)}")
            return False
        return False

    @staticmethod
    def send_verification_email(user: User) -> None:
        """Send email verification link"""
        try:
            token = jwt.encode(
                {
                    'user_id': user.id,
                    'exp': datetime.utcnow() + timedelta(days=1)
                },
                current_app.config['SECRET_KEY'],
                algorithm='HS256'
            )
            
            EmailService.send_verification_email(user.email, token)
        except Exception as e:
            current_app.logger.error(f"Send verification email error: {str(e)}")
            raise