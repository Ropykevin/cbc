from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectMultipleField, SubmitField,EmailField, SelectField, PasswordField,\
TimeField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError,Regexp,EqualTo
from app.models.curriculum import CurriculumSubject
from app.models.teacher import Teacher
from app.models.timetable import Subject


class SubjectForm(FlaskForm):

    subject = SelectField('Select Subject', coerce=int, validators=[DataRequired()])
    lessons_per_week = IntegerField('Lessons per week', default=1)
    max_consecutive_periods = IntegerField('max_consecutive_periods', default=1)

    def __init__(self, *args, **kwargs): 
        super(SubjectForm, self).__init__(*args, **kwargs)
        subjects = CurriculumSubject.query.all() 
        self.subject.choices = [(subject.id, subject.name) for subject in subjects]
    # name = StringField('Subject Name', validators=[
    #     DataRequired(),
    #     Length(min=2, max=50, message="Name must be between 2 and 50 characters")
    # ])
    
    # code = StringField('Subject Code', validators=[
    #     DataRequired(),
    #     Length(min=2, max=10),
    #     Regexp(r'^[A-Z0-9]+$', message="Code must contain only uppercase letters and numbers")
    # ])
    
    # color_code = StringField('Color Code', validators=[
    #     DataRequired(),
    #     Regexp(r'^#[0-9A-Fa-f]{6}$', message="Must be a valid hex color code (e.g., #FF0000)")
    # ], default='#FFFFFF')
    
    # max_consecutive_periods = IntegerField('Maximum Consecutive Periods', validators=[
    #     DataRequired(),
    #     NumberRange(min=1, max=4, message="Must be between 1 and 4 periods")
    # ], default=2)
    
    # lessons_per_week = IntegerField('Lessons per Week', validators=[
    #     DataRequired(),
    #     NumberRange(min=1, max=10, message="Must be between 1 and 10 lessons")
    # ], default=1)
    
    # submit = SubmitField('Save Subject')

class ClassForm(FlaskForm):
    name = StringField('Class Name', validators=[
        DataRequired(),
        Length(min=2, max=20, message="Name must be between 2 and 20 characters")
    ])
    
    grade_level = IntegerField('Grade Level', validators=[
        DataRequired(),
        NumberRange(min=1, max=12, message="Grade must be between 1 and 12")
    ])
    
    section = StringField('Section', validators=[
        DataRequired(),
        Length(max=10, message="Section identifier must not exceed 10 characters")
    ])
    
    submit = SubmitField('Save Class')
    
    def validate_name(self, field):
        if not any(c.isalpha() for c in field.data):
            raise ValidationError("Class name must contain at least one letter")
        

class TeacherForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters")
    ])

    email = EmailField('Email', validators=[
        DataRequired(),
        Email(message="Please enter a valid email address"),
        Length(max=120)
    ])

    max_hours = IntegerField('Maximum Hours per Week', validators=[
        DataRequired(),
        NumberRange(min=1, max=40, message="Hours must be between 1 and 40")
    ])

    subjects = SelectMultipleField('Teaching Subjects', coerce=int, validators=[DataRequired()])

    submit = SubmitField('Save Teacher')

class TimetableEntryForm(FlaskForm):
    day = SelectField('Day', coerce=int, validators=[DataRequired()], choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday')
    ])
    
    period = SelectField('Period', coerce=int, validators=[DataRequired()], choices=[
        (i, f'Period {i}') for i in range(1, 9)
    ])
    
    subject = SelectField('Subject', coerce=int, validators=[DataRequired()])
    teacher = SelectField('Teacher', coerce=int, validators=[DataRequired()])
    
    submit = SubmitField('Save Entry')
    
    def __init__(self, school_id, *args, **kwargs):
        super(TimetableEntryForm, self).__init__(*args, **kwargs)
        # Dynamically load subjects and teachers for the school
        self.subject.choices = [
            (s.id, s.name)
            for s in Subject.query.filter_by(school_id=school_id).order_by(Subject.name).all()
        ]
        self.teacher.choices = [
            (t.id, f"{t.user.username} ({t.teacher_code})")
            for t in Teacher.query.filter_by(school_id=school_id).all()
        ]

# profile 
class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=2, max=64)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    submit = SubmitField('Update Profile')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')


# period
class PeriodForm(FlaskForm):
    number = IntegerField('Period Number', validators=[
        DataRequired(),
        NumberRange(min=1, max=12, message="Period number must be between 1 and 12")
    ])
    
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    is_break = BooleanField('Break Period')
    
    submit = SubmitField('Save Period')
    
    def validate_end_time(self, field):
        if self.start_time.data and field.data:
            if field.data <= self.start_time.data:
                raise ValidationError("End time must be after start time")