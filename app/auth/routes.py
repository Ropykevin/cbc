from flask import Blueprint, render_template, redirect, url_for, flash, request, session,current_app
from flask_login import login_user, logout_user, current_user, login_required
from app.auth.forms import LoginForm, RegistrationForm
from app.auth.forms import (
    RegistrationStepOneForm, RegistrationStepTwoForm, RegistrationStepThreeForm,ResetPasswordRequestForm,ResetPasswordForm,\
    EditProfileForm )
from app.services.password_service import PasswordService
from app.models.user import User
from app.models.school import School
from app.auth import bp
from app.extensions import db, limiter
from app.utils.security import generate_confirmation_token, confirm_token
from app.utils.email import send_confirmation_email
from app.utils.email import send_password_reset_email
from app.auth.forms import ResetPasswordRequestForm
from app.services.auth_service import AuthService

# bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('login successful','success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Invalid email or password','danger')
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    # Initialize step if not set
    if 'registration_step' not in session:
        session['registration_step'] = 1
        session['registration_data'] = {}
    
    current_step = session.get('registration_step', 1)

    if request.method == 'POST' and 'previous' in request.form:
        session['registration_step'] = max(1, current_step - 1)
        return redirect(url_for('auth.register'))
    
    if current_step == 1:
        form = RegistrationStepOneForm()
        if form.validate_on_submit():
            session['registration_data'].update({
                'school_name': form.school_name.data,
                'email_domain': form.email_domain.data,
                'phone': form.phone.data,
                'school_type': form.school_type.data
            })
            session['registration_step'] = 2
            return redirect(url_for('auth.register'))
            
    elif current_step == 2:
        form = RegistrationStepTwoForm()
        if form.validate_on_submit():
            session['registration_data'].update({
                'admin_name': form.admin_name.data,
                'admin_email': form.admin_email.data,
                'password': form.password.data
            })
            session['registration_step'] = 3
            return redirect(url_for('auth.register'))
            
    elif current_step == 3:
        form = RegistrationStepThreeForm()
        if form.validate_on_submit():
            # Create school
            school = School(
                name=session['registration_data']['school_name'],
                email=session['registration_data']['admin_email'],
                phone=session['registration_data']['phone'],
                subscription_type='basic'
            )
            db.session.add(school)
            db.session.flush()  # Get school.id
            
            # Create admin user
            admin = User(
                username=session['registration_data']['admin_name'],
                email=session['registration_data']['admin_email'],
                role='admin',
                school_id=school.id
            )
            admin.set_password(session['registration_data']['password'])
            db.session.add(admin)
            
            try:
                db.session.commit()
                # Clear registration session data
                session.pop('registration_step', None)
                session.pop('registration_data', None)
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                flash('Registration failed. Please try again.', 'danger')
                return redirect(url_for('auth.register'))
    
    return render_template('auth/register_steps.html', 
                         form=form, 
                         current_step=current_step)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
@limiter.limit("100 per hour")
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            flash('Check your email for instructions to reset your password.', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('If this email exists in our system, you will receive reset instructions.', 'info')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/reset_password_request.html', form=form)

@bp.route('/profile')
@login_required
def profile():
    # print("mimi",current_user.username)
    return render_template('auth/profile.html', title='Profile')

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form=EditProfileForm(obj=current_user)
    user = User.query.filter_by(email=form.email.data).first()
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('auth.edit_profile'))


    return render_template('admin/profile/edit.html', title='Profile',form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        
        return redirect(url_for('main.index'))
        
    try:
        user = AuthService.verify_reset_token(token)
        print("user.......", user)
        if not user:
            flash('Invalid or expired reset link.', 'danger')
            return redirect(url_for('auth.login'))
            
        form = ResetPasswordForm()
        if form.validate_on_submit():
            AuthService.reset_password(user, form.password.data)
            flash('Your password has been reset.', 'success')
            return redirect(url_for('auth.login'))
            
        return render_template('auth/reset_password.html', form=form)
        
    except Exception as e:
        current_app.logger.error(f"Password reset error: {str(e)}")
        flash('Failed to reset password.', 'danger')
        return redirect(url_for('auth.login'))
@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

