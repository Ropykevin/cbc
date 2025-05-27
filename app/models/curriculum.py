from app.extensions import db
from datetime import datetime

class CurriculumSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    lessons_per_week = db.Column(db.Integer, default=1)
    color_code = db.Column(db.String(7), default='#FFFFFF')  # Hex color code
    max_consecutive_periods = db.Column(db.Integer, default=2)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    # teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    grade_level = db.Column(db.Integer)


class GradeLevelSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    grade_level_id = db.Column(db.Integer, db.ForeignKey('grade_level.id'), nullable=False)
    lessons_per_week = db.Column(db.Integer, nullable=False)
    is_mandatory = db.Column(db.Boolean, default=True)

    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)

    subject = db.relationship('Subject', backref='grade_level_subjects')

    # __table_args__ = (
    #     db.UniqueConstraint('subject_id', 'grade_level_id', 'school_id',
    #                        name='unique_grade_subject'),
    # )

class TeacherSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)  # Primary teaching subject
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    grade_level_id = db.Column(db.Integer, db.ForeignKey('grade_level.id'), nullable=False)  # Link grade level


    # __table_args__ = (
    #     db.UniqueConstraint('teacher_id', 'subject_id', 'grade_level_id','school_id',
    #                        name='unique_teacher_subject'),
    # )