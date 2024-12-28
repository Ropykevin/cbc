from flask import render_template, redirect, url_for,jsonify,flash, request
from flask_login import login_required, current_user
from app.admin import bp
from app.utils.security import admin_required
from app.models.teacher import Teacher
from app.models.user import User
from app.admin.forms import TeacherForm
from app.extensions import db
from app.utils.teacher_code import generate_teacher_code
from app.models.timetable import Class
from app.admin.forms import ClassForm
from app.extensions import db
from app.models.teacher import Teacher
from app.models.timetable import Class, Subject
from app.models.activity import Activity
from app.utils.security import admin_required
from app.models.curriculum import CurriculumSubject, TeacherSubject
from app.admin.forms import SubjectForm
from app.utils.security import admin_required, premium_required
from app.models.timetable import Class, TimetableEntry
from app.utils.timetable_generator import TimetableGenerator
from app.utils.activity_logger import log_activity
from app.admin.forms import ProfileForm, ChangePasswordForm
from app.models.subscription import SubscriptionTier
from app.models.activity import Activity
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload


@bp.route('/activity-log')
@login_required
@admin_required
def activity_log():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query with filters
    query = Activity.query.filter_by(school_id=current_user.school_id)
    
    # Apply filters
    action_type = request.args.get('action_type')
    if action_type:
        query = query.filter_by(action_type=action_type)
        
    entity_type = request.args.get('entity_type')
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
        
    date_from = request.args.get('date_from')
    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(Activity.timestamp >= date_from)
    
    # Order by most recent first
    query = query.order_by(Activity.timestamp.desc())
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page)
    activities = pagination.items
    
    return render_template('admin/activity_log.html',
                         activities=activities,
                         pagination=pagination)

# @bp.route('/dashboard')
# @login_required
# @admin_required
# def dashboard():
#     return render_template('admin/dashboard.html')

@bp.route('/teachers')
@login_required
@admin_required
def manage_teachers():
    # Fetch all teachers for the current user's school
    teachers = Teacher.query.filter_by(school_id=current_user.school_id).all()

    # Fetch all subjects for the current user's school
    subjects = Subject.query.filter_by(school_id=current_user.school_id).order_by(Subject.name).all()

    # Prepare subject choices for the form
    form = TeacherForm()
    form.subjects.choices = [(subject.id, f"{subject.name} ({subject.code})") for subject in subjects]

    # Map subjects to teachers
    teacher_subjects = {}
    for teacher in teachers:
        if hasattr(teacher, 'subject_list'):
            # Fetch subjects for the teacher in one query
            teacher_subjects[teacher.id] = Subject.query.filter(Subject.id.in_(teacher.subject_list)).all()

    return render_template(
        'admin/manage_teachers.html',
        teachers=teachers,
        form=form,
        teacher_subjects=teacher_subjects
    )



@bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_teacher():
    form = TeacherForm()

    # Fetch subjects for the current school
    subjects = Subject.query.filter_by(school_id=current_user.school_id).order_by(Subject.name).all()
    print("subjects..............", subjects)

    form.subjects.choices = [(subject.id, f"{subject.name} ({subject.code})") for subject in subjects]
    print('---------form.subjects.choices ------------------',form.subjects.choices)

    if form.validate_on_submit():
        try:
            # Create a new user (teacher account)
            user = User(
                username=form.full_name.data,
                email=form.email.data,
                school_id=current_user.school_id
            )
            user.set_password('changeme')  # Assign a default password
            db.session.add(user)
            db.session.flush()  # Save user to get the ID

            # Create a teacher profile
            teacher = Teacher(
                user_id=user.id,
                teacher_code=generate_teacher_code(form.full_name.data),
                max_hours_per_week=form.max_hours.data,
                school_id=current_user.school_id
            )
            db.session.add(teacher)
            db.session.flush()  # Save teacher to get the ID

            # Assign subjects to the teacher
            if form.subjects.data:
                for subject_id in form.subjects.data:
                    teacher_subject = TeacherSubject(
                        teacher_id=teacher.id,
                        subject_id=subject_id
                    )
                    db.session.add(teacher_subject)

            # Commit changes to the database
            db.session.commit()
            flash('Teacher registered successfully!', 'success')
            return redirect(url_for('main.index'))

        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback changes in case of errors
            flash(f'Failed to register teacher. Error: {e}', 'danger')
            print(f"Error: {e}")

    return render_template('admin/manage_teachers.html', form=form)



@bp.route('/teachers/<int:teacher_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    if teacher.school_id != current_user.school_id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        db.session.delete(teacher.user)  # Will cascade delete teacher record
        db.session.commit()
        return jsonify({'message': 'Teacher deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@bp.route('/classes')
@login_required
@admin_required
def manage_classes():
    classes = Class.query.filter_by(school_id=current_user.school_id).all()
    form = ClassForm()
    return render_template('admin/manage_classes.html', classes=classes, form=form)

@bp.route('/classes/add', methods=['POST'])
@login_required
@admin_required
def add_class():
    form = ClassForm()
    if form.validate_on_submit():
        class_obj = Class(
            name=form.name.data,
            grade_level=form.grade_level.data,
            school_id=current_user.school_id
        )
        db.session.add(class_obj)
        
        try:
            db.session.commit()
            flash('Class added successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Failed to add class.', 'danger')
            
    return redirect(url_for('admin.manage_classes'))

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    teachers = Teacher.query.filter_by(school_id=current_user.school_id).all()
    classes = Class.query.filter_by(school_id=current_user.school_id).all()
    subjects = Subject.query.filter_by(school_id=current_user.school_id).all()
    recent_activities = Activity.query.filter_by(
        school_id=current_user.school_id
    ).order_by(Activity.timestamp.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         teachers=teachers,
                         classes=classes,
                         subjects=subjects,
                         recent_activities=recent_activities)

# @bp.route('/subjects')
# @login_required
# @admin_required
# def manage_subjects():
#     subjects = CurriculumSubject.query.filter_by(school_id=current_user.school_id).all()
#     form = SubjectForm()
#     return render_template('admin/manage_subjects.html', subjects=subjects, form=form)

@bp.route('/subjects/add', methods=['POST'])
@login_required
@admin_required
def add_subject():
    form = SubjectForm()
    if request.method == 'GET':
        curriculum_subjects = CurriculumSubject.query.all()
        form.subject.choices = [(subject.id, subject.name) for subject in curriculum_subjects]
    if form.validate_on_submit():
        try:
            selected_subject = CurriculumSubject.query.get(form.subject.data)
            print(selected_subject)
            # Check if the subject already exists in the Subject table for this school
            existing_subject = Subject.query.filter_by(school_id=current_user.school_id, code=selected_subject.code).first()


            if not existing_subject:
                # Create a new subject record in the Subject table
                subject = Subject(
                    name=selected_subject.name,
                    code=selected_subject.code,
                    lessons_per_week=form.lessons_per_week.data,
                    max_consecutive_periods=form.max_consecutive_periods.data,
                    school_id=current_user.school_id,
                    grade_level=selected_subject.grade_level  # Automatically set from the current user's school
                )
                db.session.add(subject)
                db.session.commit()

                flash('Subject added successfully.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Failed to add subject: {str(e)}', 'danger')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
                
    subjects = Subject.query.filter_by(school_id=current_user.school_id).all()

    return render_template('admin/manage_subjects.html', form=form, subjects=subjects)

@bp.route('/subjects')
@login_required
@admin_required
def manage_subjects():
    subjects = Subject.query.filter_by(school_id=current_user.school_id).all()
    form = SubjectForm()
    return render_template('admin/manage_subjects.html', subjects=subjects, form=form)

# curriculum subjects

def populate_curriculum_subjects():
    """Populates the CurriculumSubject table with CBC subjects."""
    cbc_subjects = [
    # Lower Primary (Grade 1-3)
    {"name": "Mathematics", "code": "MATH", "lessons_per_week": 5, "color_code": "#FF5733", "max_consecutive_periods": 2, "grade_level": 1},
    {"name": "English", "code": "ENG", "lessons_per_week": 5, "color_code": "#33C1FF", "max_consecutive_periods": 2, "grade_level": 1},
    {"name": "Kiswahili", "code": "KIS", "lessons_per_week": 5, "color_code": "#3396FF", "max_consecutive_periods": 2, "grade_level": 1},
    {"name": "Environmental Activities", "code": "ENV", "lessons_per_week": 4, "color_code": "#75FF33", "max_consecutive_periods": 2, "grade_level": 1},
    {"name": "Movement and Creative Arts", "code": "ART", "lessons_per_week": 3, "color_code": "#FFB733", "max_consecutive_periods": 2, "grade_level": 1},
    {"name": "Physical and Health Education", "code": "PHE", "lessons_per_week": 2, "color_code": "#FF33C1", "max_consecutive_periods": 1, "grade_level": 1},
    {"name": "Music", "code": "MUS", "lessons_per_week": 2, "color_code": "#C133FF", "max_consecutive_periods": 1, "grade_level": 1},

    {"name": "Mathematics", "code": "MATH", "lessons_per_week": 5, "color_code": "#FF5733", "max_consecutive_periods": 2, "grade_level": 2},
    {"name": "English", "code": "ENG", "lessons_per_week": 5, "color_code": "#33C1FF", "max_consecutive_periods": 2, "grade_level": 2},
    {"name": "Kiswahili", "code": "KIS", "lessons_per_week": 5, "color_code": "#3396FF", "max_consecutive_periods": 2, "grade_level": 2},
    {"name": "Science and Technology", "code": "SCI", "lessons_per_week": 4, "color_code": "#75FF33", "max_consecutive_periods": 2, "grade_level": 2},
    {"name": "Social Studies", "code": "SOC", "lessons_per_week": 3, "color_code": "#FFC133", "max_consecutive_periods": 2, "grade_level": 2},
    {"name": "Religious Education", "code": "REL", "lessons_per_week": 2, "color_code": "#9933FF", "max_consecutive_periods": 1, "grade_level": 2},
    {"name": "Creative Arts", "code": "CRA", "lessons_per_week": 3, "color_code": "#FF33B5", "max_consecutive_periods": 1, "grade_level": 2},
    {"name": "Physical and Health Education", "code": "PHE", "lessons_per_week": 2, "color_code": "#FF33C1", "max_consecutive_periods": 1, "grade_level": 2},
    {"name": "Music", "code": "MUS", "lessons_per_week": 2, "color_code": "#C133FF", "max_consecutive_periods": 1, "grade_level": 2},


    # Junior Secondary (Grade 7-9)
    {"name": "Mathematics", "code": "MATH", "lessons_per_week": 6, "color_code": "#FF5733", "max_consecutive_periods": 2, "grade_level": 3},
    {"name": "English", "code": "ENG", "lessons_per_week": 5, "color_code": "#33C1FF", "max_consecutive_periods": 2, "grade_level": 3},
    {"name": "Kiswahili", "code": "KIS", "lessons_per_week": 5, "color_code": "#3396FF", "max_consecutive_periods": 2, "grade_level": 3},
    {"name": "Integrated Science", "code": "SCI", "lessons_per_week": 4, "color_code": "#75FF33", "max_consecutive_periods": 2, "grade_level": 3},
    {"name": "Social Studies", "code": "SOC", "lessons_per_week": 3, "color_code": "#FFC133", "max_consecutive_periods": 2, "grade_level": 3},
    {"name": "Computer Science", "code": "COMP", "lessons_per_week": 2, "color_code": "#3399FF", "max_consecutive_periods": 2, "grade_level": 3},
    {"name": "Business Studies", "code": "BIZ", "lessons_per_week": 2, "color_code": "#FF9F33", "max_consecutive_periods": 2, "grade_level": 3},
    {"name": "Agriculture", "code": "AGRI", "lessons_per_week": 3, "color_code": "#33FF57", "max_consecutive_periods": 2, "grade_level": 3},
    {"name": "Physical Education", "code": "PE", "lessons_per_week": 2, "color_code": "#FF33A1", "max_consecutive_periods": 1, "grade_level": 3},
    {"name": "Religious Education", "code": "REL", "lessons_per_week": 2, "color_code": "#9933FF", "max_consecutive_periods": 1, "grade_level": 3},
    {"name": "Music", "code": "MUS", "lessons_per_week": 2, "color_code": "#C133FF", "max_consecutive_periods": 1, "grade_level": 3},
    {"name": "Visual Arts", "code": "VART", "lessons_per_week": 2, "color_code": "#FF33D1", "max_consecutive_periods": 1, "grade_level": 3},
]
    
    try:
        for subject in cbc_subjects:
            print(subject)
            # Check if the subject already exists to prevent duplication
            existing_subject = CurriculumSubject.query.filter_by(code=subject["code"]).first()
            if not existing_subject:
                new_subject = CurriculumSubject(
                    name=subject["name"],
                    code=subject["code"],
                    lessons_per_week=subject["lessons_per_week"],
                    color_code=subject["color_code"],
                    grade_level=subject["grade_level"],
                    max_consecutive_periods=subject["max_consecutive_periods"]
                )
                db.session.add(new_subject)
                print(new_subject)

        db.session.commit()
        print("Curriculum subjects added successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Failed to populate curriculum subjects: {str(e)}")


@bp.route('/curriculum_subject', methods=["GET"])
@login_required
@admin_required
def manage_curriculumsubjects():
    subjects = CurriculumSubject.query.filter_by(school_id=current_user.school_id).all()
    return render_template('admin/manage_subjects.html', subjects=subjects)




# manage subscriptions
@bp.route('/subscription')
@login_required
@admin_required
def manage_subscription():
    current_tier = current_user.school.subscription_type
    subscription_tiers = SubscriptionTier.query.all()
    return render_template('admin/subscription/manage.html',
                         current_tier=current_tier,
                         subscription_tiers=subscription_tiers)

@bp.route('/subscription/upgrade/<string:tier_name>', methods=['POST'])
@login_required
@admin_required
def upgrade_subscription(tier_name):
    tier = SubscriptionTier.query.filter_by(name=tier_name).first_or_404()
    
    try:
        current_user.school.subscription_type = tier.name
        db.session.commit()
        flash(f'Successfully upgraded to {tier.name} subscription!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to upgrade subscription. Please try again.', 'danger')
        
    return redirect(url_for('admin.manage_subscription'))


# manage timetables

# @bp.route('/t.t')
# def timetable():
#     return render_template('generate_timetable.html')

@bp.route('/timetables')
@login_required
@admin_required
def manage_timetables():
    classes = Class.query.filter_by(school_id=current_user.school_id).all()
    subjects = Subject.query.filter_by(school_id=current_user.school_id).all()
    teachers = Teacher.query.filter_by(school_id=current_user.school_id).all()
    
    return render_template('admin/manage_timetables.html',
                         classes=classes,
                         subjects=subjects,
                         teachers=teachers)

class TimetableGenerator:
    def __init__(self, school_id, grade_level):
        self.school_id = school_id
        self.grade_level = grade_level

    def generate_class_timetable(self, class_id):
        # Fetch all subjects and teachers for the grade level
        subjects = Subject.query.filter_by(grade_level=self.grade_level).all()
        print('-------grade level-------',self.grade_level)

        print('-------subjects-------',subjects)
        teachers = Teacher.query.filter_by(school_id=self.school_id).all()
        print('-------teachers-------',teachers)

        if not subjects or not teachers:
            return None  # Fail if data is incomplete

        # Dummy timetable generation logic
        timetable = {}
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            for period in range(1, 8):  # Assume 7 periods per day
                subject = subjects[period % len(subjects)]
                teacher = teachers[period % len(teachers)]
                timetable[(day, period)] = {
                    "subject_id": subject.id,
                    "teacher_id": teacher.id
                }
        return timetable
                         
@bp.route('/timetable/<int:class_id>/generate', methods=['GET', 'POST'])
@login_required
@admin_required
# @premium_required
def generate_timetable(class_id):
    class_obj = Class.query.get_or_404(class_id)
    print('kevin======',class_obj)
    if class_obj.school_id != current_user.school_id:
        return jsonify({'error': 'Access denied'}), 403
    

    generator = TimetableGenerator(current_user.school_id, class_obj.grade_level)
    print('class id',class_id)
    timetable = generator.generate_class_timetable(class_id)
    print("ivy---------",timetable)
    
    if timetable is None:
        print('Could not generate a valid timetable. Please check teacher and subject assignments.', 'danger')
    else:
        try:
            # Clear existing entries
            TimetableEntry.query.filter_by(class_id=class_id).delete()
            
            # Create new entries
            for (day, period), data in timetable.items():
                entry = TimetableEntry(
                    day=day,
                    period=period,
                    subject_id=data['subject_id'],
                    teacher_id=data['teacher_id'],
                    class_id=class_id
                )
                print("----entry----",entry)
                db.session.add(entry)
                print("----add entry----",entry)

            
            db.session.commit()
            print('Timetable generated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Failed to save timetable.', 'danger')
    
    return redirect(url_for('admin.view_timetable', class_id=class_id))


@bp.route('/timetable/stream/<int:class_id>', methods=['GET'])
@login_required
def get_stream_timetable(class_id):
    class_obj = Class.query.get_or_404(class_id)
    timetable = TimetableEntry.query.filter_by(class_id=class_id).order_by(TimetableEntry.day, TimetableEntry.period).all()
    return render_template('stream_timetable.html', class_obj=class_obj, timetable=timetable)


@bp.route('/timetable/<int:class_id>')
@login_required
@admin_required
def view_timetable(class_id):
    class_obj = Class.query.get_or_404(class_id)
    if class_obj.school_id != current_user.school_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('admin.dashboard'))
    print("class id", class_id)
    entries = TimetableEntry.query.filter_by(class_id=class_id).all()
    print("------- entries-------" ,entries )

    timetable_data = {}
    for entry in entries:
        timetable_data[(entry.day, entry.period)] = entry
        print("------- timetable data-------" ,timetable_data.get((entry.day,entry.period)) )

    
    return render_template('timetable/view.html',
                         class_name=class_obj.name,
                         class_id=class_id,
                         entries=timetable_data)

@bp.route('/timetable/<int:class_id>/edit')
@login_required
@admin_required
# @premium_required
def edit_timetable(class_id):
    class_obj = Class.query.get_or_404(class_id)
    if class_obj.school_id != current_user.school_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    entries = TimetableEntry.query.filter_by(class_id=class_id).all()
    timetable_data = {}
    for entry in entries:
        timetable_data[(entry.day, entry.period)] = entry
    
    return render_template('admin/edit_timetable.html',
                         class_name=class_obj.name,
                         class_id=class_id,
                         entries=timetable_data)

@bp.route('/timetable')
@login_required

def timetable():
    """Admin timetable management view"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    classes = Class.query.all()
    teachers = Teacher.query.all()
    subjects = Subject.query.all()
    return render_template('admin/timetable.html',
                         classes=classes,
                         teachers=teachers,
                         subjects=subjects)


# profile
@bp.route('/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        try:
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Failed to update profile. Please try again.', 'danger')
            
    return render_template('admin/profile/edit.html', form=form)

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    password_form = ChangePasswordForm()
    if password_form.validate_on_submit():
        if current_user.check_password(password_form.current_password.data):
            try:
                current_user.set_password(password_form.new_password.data)
                db.session.commit()
                flash('Password changed successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Failed to change password. Please try again.', 'danger')
        else:
            flash('Current password is incorrect.', 'danger')
            
    return render_template('admin/profile/settings.html', form=password_form)