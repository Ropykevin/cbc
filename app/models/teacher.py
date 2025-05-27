from datetime import datetime
from app.extensions import db

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    teacher_code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subjects = db.relationship('TeacherSubject', backref='teacher', lazy=True)
    user = db.relationship('User', backref='teacher', lazy=True)
    
    timetable_entries = db.relationship(
        'TimetableEntry',
        backref='assigned_teacher',  # Enables `timetable_entry.teacher` access
        lazy='dynamic'              # Loads entries only when accessed
    )

    @property
    def teacher_name(self):
        """Fetch the name or username from the associated User."""
        return self.user.name if hasattr(self.user, 'name') else self.user.username

    @property
    def subject_list(self):
        """List of subject IDs associated with the teacher."""
        return [ts.subject_id for ts in self.subjects]
    
    @property
    def current_hours(self):
        """Current number of hours assigned to the teacher."""
        return self.timetable_entries.count()
    
    # @property
    # def available_hours(self):
    #     """Available hours the teacher can take."""
    #     return self.max_hours_per_week - self.current_hours
