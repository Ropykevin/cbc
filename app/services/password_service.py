from datetime import datetime, timedelta
from flask import current_app
import jwt
from app.extensions import db
from app.models.user import User
from app.utils.email import send_password_reset_email


class PasswordService:
    @staticmethod
    def generate_reset_token(user: User) -> str:
        """
        Generate a password reset token for the user.
        The token will expire after 1 hour.
        """
        try:
            print(user.email)
            token = jwt.encode(
                {
                    'user_id': user.id,
                    'email': user.email,
                    'exp': datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
                },
                current_app.config['SECRET_KEY'],
                algorithm='HS256'
            )
            return token
        except Exception as e:
            current_app.logger.error(f"Error generating reset token: {str(e)}")
            return None

    @staticmethod
    def verify_reset_token(token: str) -> User:
        
        print("Verify the provided password reset token.If the token is valid, return the corresponding user.")
        
        try:
            print(token)
            # Decode the token
            data = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            print(data["reset_password"])
            user = User.query.get(data['reset_password'])
            return user
        
        except jwt.ExpiredSignatureError:
            current_app.logger.error("Password reset token expired.")
        except jwt.InvalidTokenError:
            current_app.logger.error("Invalid password reset token.")
        except Exception as e:
            current_app.logger.error(f"Reset token verification error: {str(e)}")
        return None

    @staticmethod
    def reset_password(user: User, new_password: str) -> bool:
        """
        Reset the password for the user and save the changes to the database.
        """
        try:
            user.set_password(new_password)  # Assuming User model has a set_password method
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password reset failed: {str(e)}")
            return False

    @staticmethod
    def send_reset_email(user: User) -> bool:
        """
        Send a password reset email to the user.
        """
        try:
            # Generate a reset token
            token = PasswordService.generate_reset_token(user)
            if not token:
                current_app.logger.error("Failed to generate reset token.")
                return False
            
            # Use the utility function to send the email
            send_password_reset_email(user.email, token)
            return True
        except Exception as e:
            current_app.logger.error(f"Error sending password reset email: {str(e)}")
            return False