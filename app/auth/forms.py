from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField,SelectMultipleField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models.school import School

class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    
    name = StringField('name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address=StringField('Address',validators=[DataRequired()])
    phone_number=StringField('Phone', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    # role = SelectField('Role', choices=[('admin', 'user'), ('admin', 'admin')])
    submit = SubmitField('Register')
    

    def validate_username(self, name):
        user = School.query.filter_by(name=name.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = School.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
        

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(min=6, max=120)
    ])
    submit = SubmitField('Request Password Reset')


class RegistrationStepOneForm(FlaskForm):
    school_name = StringField('School Name', validators=[DataRequired(), Length(min=2, max=100)])
    email_domain = StringField('Email Domain', validators=[DataRequired(), Length(min=4, max=100)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=20)])
    school_type = SelectField('School Type', choices=[
        ('primary', 'Primary School'),
        ('secondary', 'Secondary School'),
        ('both', 'Primary and Secondary')
    ], validators=[DataRequired()])

class RegistrationStepTwoForm(FlaskForm):
    admin_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    admin_email = StringField('Work Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8),
        EqualTo('password_confirm', message='Passwords must match')
    ])
    password_confirm = PasswordField('Confirm Password')

class RegistrationStepThreeForm(FlaskForm):
    grade_levels = SelectMultipleField('Grade Levels', coerce=int, choices=[
        (i, f'Grade {i}') for i in range(1, 13)
    ], validators=[DataRequired()])
    sections_per_grade = IntegerField('Sections per Grade', validators=[DataRequired()])
    academic_structure = SelectField('Academic Year Structure', choices=[
        ('semester', 'Semester System'),
        ('trimester', 'Trimester System'),
        ('annual', 'Annual System')
    ], validators=[DataRequired()])