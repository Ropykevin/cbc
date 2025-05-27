from app.extensions import db
import random

class GradeLevel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))

    classes = db.relationship('ClassStream', backref='grade_level', lazy=True)
    


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    lessons_per_week = db.Column(db.Integer, default=1)
    grade_level_id = db.Column(db.Integer, db.ForeignKey('grade_level.id'))
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    max_consecutive_periods= db.Column(db.Integer, nullable=False)

# streams per grade level
class ClassStream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    grade_level_id = db.Column(db.Integer, db.ForeignKey('grade_level.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))

    timetable_entries = db.relationship('TimetableEntry', backref='class_stream', lazy=True)

    def generate_timetable_grade_1_3(self, subjects, teacher):
        """
        Generate a timetable for Grade 1-3 where one teacher teaches all subjects in a stream.
        Ensures all periods are filled by repeating subjects as needed.
        """
        timetable = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
        
        # Clear existing timetable entries for the class and teacher
        existing_entries = TimetableEntry.query.filter_by(class_id=self.id, teacher_id=teacher.id).all()
        for entry in existing_entries:
            db.session.delete(entry)
        db.session.commit()  # Commit to remove existing entries

        # Prepare a list of subjects based on their minimum lessons per week
        subject_list = []
        for grade_level_subject in subjects:  # subjects is a list of GradeLevelSubject instances
            subject = grade_level_subject.subject
            lessons_per_week = grade_level_subject.lessons_per_week
            subject_list.extend([subject] * lessons_per_week)
        
        # Calculate the total number of periods needed
        max_periods = 8
        days = list(timetable.keys())
        total_periods = max_periods * len(days)
        
        # Fill the remaining periods by repeating subjects cyclically
        while len(subject_list) < total_periods:
            for grade_level_subject in subjects:
                subject = grade_level_subject.subject
                subject_list.append(subject)
                if len(subject_list) >= total_periods:
                    break
        
        # Shuffle the subject list for random distribution
        random.shuffle(subject_list)

        # Schedule lessons
        lesson_index = 0
        for day in days:
            for period in range(max_periods):
                if lesson_index < len(subject_list):
                    subject = subject_list[lesson_index]

                    # Add the timetable entry
                    timetable_entry = TimetableEntry(
                        day=day,
                        period=period,
                        subject_id=subject.id,
                        teacher_id=teacher.id,
                        class_id=self.id
                    )
                    db.session.add(timetable_entry)
                    timetable[day].append({
                        'lesson': period + 1,
                        'subject_name': subject.name,
                        'teacher_name': teacher.user.username
                    })
                    lesson_index += 1

        # Commit changes to the database
        db.session.commit()
        print("-------timetable-------", timetable)
        return timetable
    
    



class TimetableEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, nullable=False)  # 0-4 for Monday-Friday
    period = db.Column(db.Integer, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('class_stream.id'))
    
    # Relationships
    teacher = db.relationship('Teacher')
    subject = db.relationship('Subject', backref='timetable_entries')
    
    __table_args__ = (
        db.UniqueConstraint('day', 'period', 'class_id', 
                           name='unique_class_timeslot'),
   
    )

    @property
    def subject_name(self):
        """Fetch the subject name from the subject relationship."""
        return self.subject.name if self.subject else "N/A"

    @property
    def teacher_name(self):
        """Fetch the teacher name from the teacher relationship."""
        return self.teacher.user.username if self.teacher else "N/A"
