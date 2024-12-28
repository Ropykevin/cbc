from app.extensions import db

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    grade_level = db.Column(db.Integer, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    timetable_entries = db.relationship('TimetableEntry', backref='class', lazy=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    lessons_per_week = db.Column(db.Integer, default=1)
    grade_level = db.Column(db.Integer, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)

    max_consecutive_periods= db.Column(db.Integer, nullable=False)

class TimetableEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, nullable=False)  # 0-4 for Monday-Friday
    period = db.Column(db.Integer, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    
    # Relationships
    teacher = db.relationship('Teacher')
    subject = db.relationship('Subject', backref='timetable_entries')
    
    __table_args__ = (
        db.UniqueConstraint('day', 'period', 'class_id', 
                           name='unique_class_timeslot'),
        db.UniqueConstraint('day', 'period', 'teacher_id', 
                           name='unique_teacher_timeslot'),
    )

    @property
    def subject_name(self):
        """Fetch the subject name from the subject relationship."""
        return self.subject.name if self.subject else "N/A"

    @property
    def teacher_name(self):
        """Fetch the teacher name from the teacher relationship."""
        return self.teacher.user.username if self.teacher else "N/A"
