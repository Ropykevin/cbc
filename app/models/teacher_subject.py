from app.extensions import db
from datetime import datetime

class TeacherSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    subject = db.relationship('Subject', backref='teacher_subjects')
    
    # @property
    # def subject_list(self):
    #     return [ts.subject_id for ts in self.subjects]
    
    
    __table_args__ = (
        db.UniqueConstraint('teacher_id', 'subject_id',
                           name='unique_teacher_subject'),
    )