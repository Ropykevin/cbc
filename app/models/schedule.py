from app.extensions import db
from datetime import datetime

class Period(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_break = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        db.UniqueConstraint('school_id', 'number', name='unique_period_number'),
    )

class ScheduleChange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timetable_entry_id = db.Column(db.Integer, db.ForeignKey('timetable_entry.id'))
    changed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    previous_teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    new_teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    previous_subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    new_subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    change_date = db.Column(db.DateTime, default=datetime.utcnow)
    notification_sent = db.Column(db.Boolean, default=False)