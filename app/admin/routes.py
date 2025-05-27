from flask import render_template, redirect, url_for,jsonify,flash, request
from flask_login import login_required, current_user
from app.admin import bp
from app.utils.security import admin_required
from app.models.teacher import Teacher
from app.models.user import User
from app.admin.forms import TeacherForm
from app.extensions import db
from app.utils.teacher_code import generate_teacher_code
from app.models.timetable import ClassStream
from app.admin.forms import ClassForm
from app.extensions import db
from app.models.teacher import Teacher
from app.models.timetable import ClassStream, Subject
from app.models.activity import Activity
from app.utils.security import admin_required
from app.models.curriculum import CurriculumSubject, TeacherSubject, GradeLevelSubject
from app.admin.forms import SubjectForm
from app.utils.security import admin_required, premium_required
from app.models.timetable import ClassStream, TimetableEntry,GradeLevel
from app.utils.timetable_generator import TimetableGenerator
from app.utils.activity_logger import log_activity
from app.admin.forms import ProfileForm, ChangePasswordForm,AssignTimetableForm
from app.models.subscription import SubscriptionTier
from app.models.activity import Activity
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
import random



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


# dashboard
@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    teachers = Teacher.query.filter_by(school_id=current_user.school_id).all()
    classes = ClassStream.query.filter_by(school_id=current_user.school_id).all()
    subjects = Subject.query.filter_by(school_id=current_user.school_id).all()
    recent_activities = Activity.query.filter_by(
        school_id=current_user.school_id
    ).order_by(Activity.timestamp.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         teachers=teachers,
                         classes=classes,
                         subjects=subjects,
                         recent_activities=recent_activities)

# manage grade levels.
# automatically populate the gradeLevel table everytime the system is started
def populate_grade_levels():
    # Check if the table is empty, and if so, populate with grades 1-12
    if not GradeLevel.query.first():  # Only populate if no GradeLevels exist
        for grade in range(1, 13):  # Grades 1 to 12
            grade_level = GradeLevel(name=str(grade))
            db.session.add(grade_level)
        db.session.commit()
        print("Grade levels populated.")

    
    
# classes
@bp.route('/classes')
@login_required
@admin_required
def manage_classes():
    classes = ClassStream.query.filter_by(school_id=current_user.school_id).all()
    form = ClassForm()

    gradelevels = GradeLevel.query.all()
    print("GradeLevels from DB:", gradelevels)  # Debug: Check GradeLevel query result


    # grade level teachers
    teachers=Teacher.query.filter_by(school_id=current_user.school_id).all()
    teacher_subjects = {}
    for teacher in teachers:
        if hasattr(teacher, 'subject_list'):
            # Fetch subjects for the teacher in one query
            teacher_subjects[teacher.id] = Subject.query.filter(Subject.id.in_(teacher.subject_list)).all()

    print("Teacher Subjects:", teacher_subjects)  # Debug: Check teacher subjects
    # subject names for each grade level
    
    
    grade_level_subjects = {}

    for grade_level in gradelevels:
        grade_level_subjects[grade_level.id] = [
            gls.subject.name  # Access subject name using the relationship
            for gls in GradeLevelSubject.query
            .filter_by(grade_level_id=grade_level.id, school_id=current_user.school_id)
            .join(Subject, GradeLevelSubject.subject_id == Subject.id)  # Join with Subject table
            .options(db.joinedload(GradeLevelSubject.subject))  # Load subject data
            .all()
        ]
        print(f"Grade Level {grade_level.id} Subjects:", grade_level_subjects[grade_level.id])  # Debug: Check subjects for each grade level

    grade_level_teachers = {}

    for grade_level in gradelevels:
        grade_level_teachers[grade_level.id] = [
            teacher.user.username  # Access username from the User model through Teacher
            for teacher in Teacher.query
            .join(TeacherSubject, Teacher.id == TeacherSubject.teacher_id)
            .filter(TeacherSubject.grade_level_id == grade_level.id, TeacherSubject.school_id == current_user.school_id)
            .join(User, Teacher.user_id == User.id)  # Ensure we join User from Teacher
            .options(db.joinedload(Teacher.user))  # Load User details efficiently
            .all()
        ]
        print(f"Grade Level {grade_level.id} Teachers:", grade_level_teachers[grade_level.id])  # Debug: Check teachers for each grade level
        # grade_level_teachers[grade_level.id] = [glt.teacher.user.username for glt in teachers]

    if form.validate_on_submit():
        print("Selected Grade Level ID:", form.grade_level.data)  # Debug print
        class_obj = ClassStream(
            name=form.name.data,
            grade_level_id=form.grade_level.data,  # This should be an integer value
            school_id=current_user.school_id
        )

    form.grade_level.choices = [(level.id, level.name) for level in gradelevels]
    return render_template('admin/manage_classes.html', 
                           classes=classes, 
                           form=form, 
                           grade_level_subjects=grade_level_subjects,
                           grade_level_teachers=grade_level_teachers,
                           grade_levels=gradelevels,
                           teacher_subjects=teacher_subjects)

@bp.route('/classes/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_class():
   
    form = ClassForm()
    gradelevels = GradeLevel.query.all()
    form.grade_level.choices = [(level.id, level.name) for level in gradelevels]
    teachers=Teacher.query.filter_by(school_id=current_user.school_id).all()
  
    print("Form Choices: ", form.grade_level.choices)  # Debug: Verify choices
    
    if form.validate_on_submit():
        print("Selected Grade Level ID:", form.grade_level.data)  # Debug print
        class_obj = ClassStream(
            name=form.name.data,
            grade_level_id=form.grade_level.data,  # This should be an integer value
            school_id=current_user.school_id
        )

            
        print(f"ClassStream Object: {class_obj}")  # Debug print
        
        db.session.add(class_obj)
        
        try:
            db.session.commit()
            flash('ClassStream added successfully.', 'success')
            return redirect(url_for('admin.manage_classes'))  # Redirect after successful submit
        except Exception as e:
            db.session.rollback()
            flash('Failed to add class.', 'danger')
            # Optionally log the error for debugging
            print(f"Error: {e}")
    
    # Return the form with errors if validation failed or exception occurred
    return render_template('admin/add_class.html', form=form)

@bp.route('/subjects')
@login_required
@admin_required
def manage_subjects():
    subjects = Subject.query.filter_by(school_id=current_user.school_id).all()
    gradelevels = GradeLevel.query.all()

    form = SubjectForm()
    form.grade_level.choices = [(level.id, level.name) for level in gradelevels]
    
    # Fetching all grade levels for each subject
    subject_grade_levels = {}
    for subject in subjects:
        # Use the relationship to fetch associated grade levels
        grade_levels = [
            grade_level_subject.grade_level_id
            for grade_level_subject in subject.grade_level_subjects
        ]
        subject_grade_levels[subject.id] = grade_levels

    print("Subject Grade Levels:", subject_grade_levels)

    curriculum_subjects = CurriculumSubject.query.all()
    form.subject.choices = [(subject.id, subject.name) for subject in curriculum_subjects]
    
    # Ensure subject_grade_levels is passed to the template
    return render_template('admin/manage_subjects.html', 
                           subjects=subjects, form=form)


@bp.route('/subjects/add', methods=['POST'])
@login_required
@admin_required
def add_subject():
    form = SubjectForm()

    # Populate the grade levels as multi-select options
    gradelevels = GradeLevel.query.all()
    form.grade_level.choices = [(level.id, level.name) for level in gradelevels]

    # Populate the curriculum subjects
    curriculum_subjects = CurriculumSubject.query.all()
    form.subject.choices = [(subject.id, subject.name) for subject in curriculum_subjects]

    print("Form Data:", request.form)

    if form.validate_on_submit():
        try:
            # Fetch the selected subject
            selected_subject = CurriculumSubject.query.get(form.subject.data)
            print(selected_subject)

            # Check if the subject already exists in the Subject table for this school
            existing_subject = Subject.query.filter_by(
                school_id=current_user.school_id,
                code=selected_subject.code
            ).first()

            # If the subject does not exist, create it
            if not existing_subject:
                subject = Subject(
                    name=selected_subject.name,
                    code=selected_subject.code,
                    lessons_per_week=selected_subject.lessons_per_week,
                    max_consecutive_periods=selected_subject.max_consecutive_periods,
                    school_id=current_user.school_id
                )
                print("Creating new subject...", subject)
                db.session.add(subject)
                db.session.commit()  # Commit to get the subject ID
                print("Subject added successfully.")
            else:
                subject = existing_subject

            # Add subject to multiple grade levels
            for grade_level_id in form.grade_level.data:
                print(f"Adding subject to grade level: {grade_level_id}")
                
                # Check if the subject is already linked to this grade level
                existing_grade_level_subject = GradeLevelSubject.query.filter_by(
                    subject_id=subject.id,
                    grade_level_id=grade_level_id,
                    school_id=current_user.school_id
                ).first()

                if not existing_grade_level_subject:
                    grade_level_subject = GradeLevelSubject(
                        subject_id=subject.id,
                        grade_level_id=grade_level_id,
                        lessons_per_week=selected_subject.lessons_per_week,
                        is_mandatory=True,  
                        school_id=current_user.school_id
                    )
                    db.session.add(grade_level_subject)
                    print(f"Linked subject {subject.name} to grade level {grade_level_id}")

            db.session.commit()  # Commit the transaction for the grade level associations
            flash('Subject added to the selected grade levels successfully.', 'success')
            return redirect(url_for('admin.manage_subjects'))

        except IntegrityError as e:
            db.session.rollback()
            flash('Failed to add subject. Subject already exists.', 'danger')
            print(f"IntegrityError: {e}")


@bp.route('/subjects/delete/<int:subject_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_subject(subject_id):
    try:
        # Fetch the subject to be deleted
        subject = Subject.query.filter_by(id=subject_id, school_id=current_user.school_id).first()
        
        if not subject:
            flash("Subject not found or not authorized to delete.", "danger")
            return redirect(url_for('admin.manage_subjects'))

        # Delete all related entries in GradeLevelSubject
        GradeLevelSubject.query.filter_by(subject_id=subject_id).delete()

        # Delete the subject
        db.session.delete(subject)
        db.session.commit()

        flash("Subject and its related grade levels deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting subject: {e}")
        flash(f"An error occurred: {e}", "danger")

    return redirect(url_for('admin.manage_subjects'))


# curriculum subjects

def populate_curriculum_subjects():
    """Populates the CurriculumSubject table with CBC subjects."""
    cbc_subjects = [
    # Lower Primary (Grade 1-3)
    {"name": "Mathematics", "code": "MATH", "lessons_per_week": 5, "color_code": "#FF5733", "max_consecutive_periods": 2},
    {"name": "English", "code": "ENG", "lessons_per_week": 5, "color_code": "#33C1FF", "max_consecutive_periods": 2},
    {"name": "Kiswahili", "code": "KIS", "lessons_per_week": 5, "color_code": "#3396FF", "max_consecutive_periods": 2},
    {"name": "Environmental Activities", "code": "ENV", "lessons_per_week": 4, "color_code": "#75FF33", "max_consecutive_periods": 2},
    {"name": "Movement and Creative Arts", "code": "ART", "lessons_per_week": 3, "color_code": "#FFB733", "max_consecutive_periods": 2},
    {"name": "Physical and Health Education", "code": "PHE", "lessons_per_week": 2, "color_code": "#FF33C1", "max_consecutive_periods": 1},
    {"name": "Music", "code": "MUS", "lessons_per_week": 2, "color_code": "#C133FF", "max_consecutive_periods": 1},

    {"name": "Mathematics", "code": "MATH", "lessons_per_week": 5, "color_code": "#FF5733", "max_consecutive_periods": 2},
    {"name": "English", "code": "ENG", "lessons_per_week": 5, "color_code": "#33C1FF", "max_consecutive_periods": 2},
    {"name": "Kiswahili", "code": "KIS", "lessons_per_week": 5, "color_code": "#3396FF", "max_consecutive_periods": 2},
    {"name": "Science and Technology", "code": "SCI", "lessons_per_week": 4, "color_code": "#75FF33", "max_consecutive_periods": 2},
    {"name": "Social Studies", "code": "SOC", "lessons_per_week": 3, "color_code": "#FFC133", "max_consecutive_periods": 2},
    {"name": "Religious Education", "code": "REL", "lessons_per_week": 2, "color_code": "#9933FF", "max_consecutive_periods": 1},
    {"name": "Creative Arts", "code": "CRA", "lessons_per_week": 3, "color_code": "#FF33B5", "max_consecutive_periods": 1},
    {"name": "Physical and Health Education", "code": "PHE", "lessons_per_week": 2, "color_code": "#FF33C1", "max_consecutive_periods": 1},
    {"name": "Music", "code": "MUS", "lessons_per_week": 2, "color_code": "#C133FF", "max_consecutive_periods": 1},


    # Junior Secondary (Grade 7-9)
    {"name": "Mathematics", "code": "MATH", "lessons_per_week": 6, "color_code": "#FF5733", "max_consecutive_periods": 2},
    {"name": "English", "code": "ENG", "lessons_per_week": 5, "color_code": "#33C1FF", "max_consecutive_periods": 2},
    {"name": "Kiswahili", "code": "KIS", "lessons_per_week": 5, "color_code": "#3396FF", "max_consecutive_periods": 2},
    {"name": "Integrated Science", "code": "SCI", "lessons_per_week": 4, "color_code": "#75FF33", "max_consecutive_periods": 2},
    {"name": "Social Studies", "code": "SOC", "lessons_per_week": 3, "color_code": "#FFC133", "max_consecutive_periods": 2},
    {"name": "Computer Science", "code": "COMP", "lessons_per_week": 2, "color_code": "#3399FF", "max_consecutive_periods": 2},
    {"name": "Business Studies", "code": "BIZ", "lessons_per_week": 2, "color_code": "#FF9F33", "max_consecutive_periods": 2},
    {"name": "Agriculture", "code": "AGRI", "lessons_per_week": 3, "color_code": "#33FF57", "max_consecutive_periods": 2},
    {"name": "Physical Education", "code": "PE", "lessons_per_week": 2, "color_code": "#FF33A1", "max_consecutive_periods": 1},
    {"name": "Religious Education", "code": "REL", "lessons_per_week": 2, "color_code": "#9933FF", "max_consecutive_periods": 1},
    {"name": "Music", "code": "MUS", "lessons_per_week": 2, "color_code": "#C133FF", "max_consecutive_periods": 1},
    {"name": "Visual Arts", "code": "VART", "lessons_per_week": 2, "color_code": "#FF33D1", "max_consecutive_periods": 1},
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

# teachers
@bp.route('/teachers')
@login_required
@admin_required
def manage_teachers():
    # Fetch all teachers for the current user's school
    teachers = Teacher.query.filter_by(school_id=current_user.school_id).all()

    # Fetch all subjects for the current user's school

    # Prepare subject choices for the form
    form = TeacherForm()
    gradelevels = GradeLevel.query.all()
    subjects = Subject.query.filter_by(school_id=current_user.school_id).order_by(Subject.name).all()
    form.grade_level.choices = [(level.id, level.name) for level in gradelevels]
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

    gradelevels = GradeLevel.query.all()
    form.grade_level.choices = [(level.id, level.name) for level in gradelevels]

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
                # max_hours_per_week=form.max_hours.data,
                school_id=current_user.school_id
            )
            db.session.add(teacher)
            db.session.flush()  # Save teacher to get the ID

            # Assign subjects to the teacher
            if form.subjects.data and form.grade_level.data:
                print("form.subjects.data", form.subjects.data)
                print("form.gragelevel.data", form.grade_level.data)
                for subject_id in form.subjects.data:
                    for grade_level_id in form.grade_level.data:
                        teacher_subject = TeacherSubject(
                            teacher_id=teacher.id,
                            subject_id=subject_id,
                            grade_level_id=grade_level_id,  # Assign grade level
                            school_id=current_user.school_id
                        )
                        db.session.add(teacher_subject)

            # Commit changes to the database
            db.session.commit()
            flash('Teacher registered successfully!', 'success')
            return redirect(url_for('admin.manage_teachers'))

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
        # Delete records from TeacherSubject table
        TeacherSubject.query.filter_by(teacher_id=teacher.id).delete()

        # Delete the associated User record
        user = User.query.get(teacher.user_id)
        if user:
            db.session.delete(user)

        # Delete the Teacher record
        db.session.delete(teacher)

        # Commit the transaction
        db.session.commit()
        return jsonify({'message': 'Teacher deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

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
    classes = ClassStream.query.filter_by(school_id=current_user.school_id).all()
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
    

# # get timetable html
# @bp.route('/get_timetable_html/<int:class_id>')
# def get_timetable_html(class_id):
    
#     return render_template('admin/timetable.html', timetable_data=timetable_data)

@bp.route('/timetables/new', methods=['GET'])
@login_required
@admin_required
def new_timetable():
    # Fetch grade levels, streams, and subjects
    grade_levels = GradeLevel.query.all()
    streams = ClassStream.query.filter_by(school_id=current_user.school_id).all()
    subjects = Subject.query.filter_by(school_id=current_user.school_id).order_by(Subject.name).all()
    teachers=Teacher.query.filter_by(school_id=current_user.school_id).all()
    # filter subjects by grade level and school
    grade_level_subjects = {}
    for grade_level in grade_levels:
        grade_level_subjects[grade_level.id] = GradeLevelSubject.query.filter_by(
            grade_level_id=grade_level.id, school_id=current_user.school_id
        ).all()
    print(grade_level_subjects)

    # Initialize the form and populate choices
    form = AssignTimetableForm()
    form.grade_level.choices = [(level.id, level.name) for level in grade_levels]
    form.stream.choices = [(stream.id, stream.name) for stream in streams]
    form.subjects.choices = [(subject.id, f"{subject.name} ({subject.code})") for subject in subjects]
    form.teacher.choices = [(teacher.id, teacher.user.username) for teacher in teachers]

    # Render the form
    return render_template('admin/generate_timetable.html',
                            form=form, 
                            grade_level_subjects=grade_level_subjects,
                            grade_levels=grade_levels
                            )


@bp.route('/timetables/create', methods=['POST'])
@login_required
@admin_required
def generate_timetable():
    # Initialize the form (choices must be populated for validation)
    
    form = AssignTimetableForm()
    grade_levels = GradeLevel.query.all()
    streams = ClassStream.query.filter_by(school_id=current_user.school_id).all()
    subjects = Subject.query.filter_by(school_id=current_user.school_id).order_by(Subject.name).all()
    teachers=Teacher.query.filter_by(school_id=current_user.school_id).all()

    form.grade_level.choices = [(level.id, level.name) for level in grade_levels]
    form.stream.choices = [(stream.id, stream.name) for stream in streams]
    form.subjects.choices = [(subject.id, f"{subject.name} ({subject.code})") for subject in subjects] 
    form.teacher.choices = [(teacher.id, teacher.user.username) for teacher in teachers]
    print('form.teacher.choices',form.teacher.choices)

    # Validate the form
    if form.validate_on_submit():
        # Fetch the selected grade level and stream
        selected_grade_level = GradeLevel.query.get(form.grade_level.data)
        stream = ClassStream.query.get(form.stream.data)

        # Debugging output
        print(f"Selected Grade Level: {selected_grade_level.name}")
        print(f"Selected Stream: {stream.name}")

        # Fetch subjects for the selected grade level and stream
        selected_subjects = GradeLevelSubject.query.filter_by(
            grade_level_id=selected_grade_level.id,
            school_id=current_user.school_id
        ).all()

        # Debugging output
        print(f"Selected Subjects: {selected_subjects}")
        teacher = Teacher.query.get(form.teacher.data)
        print(f"Selected Teacher: {teacher}")

        # Generate timetable
        stream.generate_timetable_grade_1_3(selected_subjects, teacher)

        # Flash success message
        flash(f'Timetable successfully created for {stream.name} in Grade {selected_grade_level.name}.', 'success')
        return redirect(url_for('admin.new_timetable'))

    # If validation fails, re-render the form with errors

    return render_template('admin/generate_timetable.html', form=form)

@bp.route('/generate-timetable-grade-4-7', methods=['GET'])
def get_timetable_form():
    # Return the HTML form page to generate timetable
    return render_template('admin/manage_timetable2.html')


@bp.route('/generate-timetable-grade-4-6', methods=['POST'])
def generate_timetable2():

        if request.method == 'POST':
            class_id = request.form['class_stream_id']
            print("generate timetable 4-6 function working.......")
            try:
                class_id = int(class_id)
            except ValueError:
                return jsonify({"error": "Class stream ID must be an integer"}), 400

            if not class_id:
                return jsonify({"error": "Class stream ID is required"}), 400

            # Fetch the class stream for which the timetable is being generated
            class_stream = ClassStream.query.get(class_id)
            if not class_stream:
                return jsonify({"error": "Class stream not found"}), 404

            # Get the grade level ID associated with the class stream
            grade_level_id = class_stream.grade_level_id  # Assuming `ClassStream` has a `grade_level_id` attribute

            # Fetch teachers and their assigned subjects for the given grade level
            teacher_subjects = TeacherSubject.query.filter_by(grade_level_id=grade_level_id).all()

            # Map teachers and their subjects
            teachers = {}
            for teacher_subject in teacher_subjects:
                teacher = Teacher.query.get(teacher_subject.teacher_id)
                subject = Subject.query.get(teacher_subject.subject_id)

                if teacher.id not in teachers:
                    teachers[teacher.id] = {
                        'teacher': teacher,
                        'subjects': set(),
                    }
                teachers[teacher.id]['subjects'].add(subject.id)

            # Fetch all subjects for the grade level
            subjects = Subject.query.filter_by(grade_level_id=grade_level_id).all()
            subject_lessons_per_week = {subject.id: subject.lessons_per_week for subject in subjects}

            # Max periods per day
            max_periods = 8
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            total_periods = max_periods * len(days)

            # Prevent double-booking by creating a dictionary to track teacher assignments
            teacher_schedule = {
                teacher_id: {day: [None] * max_periods for day in days}
                for teacher_id in teachers.keys()
            }

            # Initialize timetable structure
            timetable = {day: [] for day in days}

            # Prepare a list of subjects for distribution
            subject_queue = []
            for subject in subjects:
                subject_queue.extend([subject] * subject_lessons_per_week[subject.id])

            # Shuffle subject queue for fairness
            random.shuffle(subject_queue)

            # Helper function to check if a subject can be scheduled in the current period
            def can_schedule_subject(day, period, subject_id, teacher_id):
                # Check if the subject can be scheduled in the current period
                if period > 0 and 'subject_id' in timetable[day][period - 1] and timetable[day][period - 1]['subject_id'] == subject_id:
                    return False  # No consecutive lessons for the same subject
                if teacher_schedule[teacher_id][day][period] is not None:
                    return False  # Teacher is already booked for this period
                return True

            # Scheduling lessons
            for day in days:
                for period in range(max_periods):
                    # Handle specific constraints
                    if period >= 4:  # Maths, English, and Kiswahili must be in the first 4 periods
                        subject_queue = [
                            s for s in subject_queue
                            if s.name not in ["Maths", "English", "Kiswahili"]
                        ]
                    if period % 2 == 1 and "Creative Arts" in [s.name for s in subject_queue]:
                        subject_queue = [
                            s for s in subject_queue
                            if s.name != "Creative Arts"
                        ]

                    # Assign the next valid subject and teacher
                    for subject in list(subject_queue):  # Iterate through the subject queue
                        assigned = False
                        for teacher_id, teacher_info in teachers.items():
                            if subject.id in teacher_info['subjects'] and can_schedule_subject(day, period, subject.id, teacher_id):
                                # Schedule the lesson
                                timetable_entry = TimetableEntry(
                                    day=day,
                                    period=period,
                                    subject_id=subject.id,
                                    teacher_id=teacher_id,
                                    class_id=class_stream.id
                                )
                                db.session.add(timetable_entry)

                                # Add the lesson to the timetable
                                timetable[day].append({
                                    'lesson': period + 1,
                                    'subject_name': subject.name,
                                    'teacher_name': teacher_info['teacher'].user.username,
                                    'subject_id': subject.id,  # Added subject_id to the timetable entry
                                })

                                # Update schedules
                                teacher_schedule[teacher_id][day][period] = subject.id
                                subject_queue.remove(subject)
                                assigned = True
                                break
                        if assigned:
                            break  # Move to the next period


            # Commit changes to the database
            db.session.commit()
            print("Timetable generated successfully.", timetable)

            return jsonify(timetable), 200
        
        return jsonify({"error": "Invalid request method"}), 405
        
        
        




@bp.route('/timetable/<int:class_id>')
@login_required
@admin_required
def view_timetable(class_id):
    class_obj = ClassStream.query.get_or_404(class_id)
    if class_obj.school_id != current_user.school_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('admin.dashboard'))
    print("class id", class_id)
    entries = TimetableEntry.query.filter_by(class_id=class_id).all()
    print("------- entries-------" ,entries )
    existing_entries = TimetableEntry.query.filter_by(class_id=class_id).all()
    for entry in existing_entries:
        db.session.delete(entry)
    db.session.commit()
    
    timetable_data = {}
    for entry in entries:
        timetable_data[(entry.day, entry.period)] = entry
        print("------- timetable data-------" ,timetable_data.get((entry.day,entry.period)) )

    
    return render_template('timetable/view.html',
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
    classes = ClassStream.query.all()
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


