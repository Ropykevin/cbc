from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField,SelectMultipleField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models.school import School
import re

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
        ('both', 'Primary and Secondary'),
        ('other', 'Other')
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
#     grade_levels = SelectMultipleField('Grade Levels', coerce=int, choices=[
#         (i, f'Grade {i}') for i in range(1, 13)
#     ], validators=[DataRequired()])
#     sections_per_grade = IntegerField('Sections per Grade', validators=[DataRequired()])
    academic_structure = SelectField('Academic Year Structure', choices=[
        ('semester', 'three-term System'),
        ('trimester', 'two-term System'),
        ('annual', 'One-term System')
    ], validators=[DataRequired()])
    
class ResetPasswordForm(FlaskForm):
        password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    
        confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    
        submit = SubmitField('Reset Password')
    
        def validate_password(self, field):
            """Validate password strength"""
            password = field.data
            
            if not re.search(r'[A-Z]', password):
                raise ValidationError('Password must contain at least one uppercase letter')
                
            if not re.search(r'[a-z]', password):
                raise ValidationError('Password must contain at least one lowercase letter')
                
            if not re.search(r'\d', password):
                raise ValidationError('Password must contain at least one number')
                
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError('Password must contain at least one special character')
            

class EditProfileForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Work Email', validators=[DataRequired(), Email()])
    