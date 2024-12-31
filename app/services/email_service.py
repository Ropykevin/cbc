from typing import Optional, List
from flask import current_app, render_template
from flask_mail import Message
from threading import Thread
from app.extensions import mail

class EmailService:
    @classmethod
    def send_async_email(cls, app, msg: Message) -> None:
        """Send email asynchronously"""
        with app.app_context():
            try:
                mail.send(msg)
            except Exception as e:
                current_app.logger.error(f"Failed to send email: {str(e)}")

    @classmethod
    def send_email(cls, subject: str, recipients: List[str], 
                  template: str, **kwargs) -> None:
        """Send email using template"""
        try:
            msg = Message(
                subject=subject,
                recipients=recipients,
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            
            # Render both HTML and text versions
            msg.html = render_template(f'email/{template}.html', **kwargs)
            msg.body = render_template(f'email/{template}.txt', **kwargs)
            
            # Send asynchronously
            Thread(
                target=cls.send_async_email,
                args=(current_app._get_current_object(), msg)
            ).start()
            
        except Exception as e:
            current_app.logger.error(f"Error preparing email: {str(e)}")
            raise

    @classmethod
    def send_verification_email(cls, email: str, token: str) -> None:
        """Send email verification link"""
        cls.send_email(
            subject='Verify Your Email',
            recipients=[email],
            template='verification',
            token=token
        )

    @classmethod
    def send_password_reset_email(cls, email: str, token: str) -> None:
        """Send password reset link"""
        cls.send_email(
            subject='Reset Your Password',
            recipients=[email],
            template='password_reset',
            token=token
        )

    @classmethod
    def send_welcome_email(cls, email: str, username: str) -> None:
        """Send welcome email to new users"""
        cls.send_email(
            subject='Welcome to School Timetable Manager',
            recipients=[email],
            template='welcome',
            username=username
        )

    @classmethod
    def send_schedule_change_notification(cls, email: str, changes: dict) -> None:
        """Send notification about schedule changes"""
        cls.send_email(
            subject='Schedule Change Notification',
            recipients=[email],
            template='schedule_change',
            changes=changes
        )