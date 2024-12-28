from typing import List
from flask import current_app
from app.extensions import db
from app.models.schedule import ScheduleChange
from app.utils.email import send_email

def notify_schedule_change(change: ScheduleChange) -> None:
    """Send notifications for schedule changes to affected teachers"""
    affected_teachers = []
    
    if change.previous_teacher_id:
        affected_teachers.append(change.previous_teacher_id)
    if change.new_teacher_id:
        affected_teachers.append(change.new_teacher_id)
    
    for teacher_id in affected_teachers:
        teacher = User.query.get(teacher_id)
        if teacher:
            send_schedule_change_email(teacher, change)
    
    change.notification_sent = True
    db.session.commit()

def send_schedule_change_email(teacher: User, change: ScheduleChange) -> None:
    """Send email notification about schedule change"""
    subject = "Schedule Change Notification"
    send_email(
        subject=subject,
        recipients=[teacher.email],
        text_body=render_template(
            'email/schedule_change.txt',
            teacher=teacher,
            change=change
        ),
        html_body=render_template(
            'email/schedule_change.html',
            teacher=teacher,
            change=change
        )
    )