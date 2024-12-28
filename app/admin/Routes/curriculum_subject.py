# from app.models.curriculum import CurriculumSubject
# from app.extensions import db
# from app.admin import bp
# from flask import flash,render_template, redirect, url_for
# from flask_login import login_required, current_user
# from app.utils.security import admin_required



# @bp.route('/populate_curriculum_subjects', methods=['POST'])
# @login_required
# @admin_required
# def populate_curriculum_subjects():
#     """Populates the CurriculumSubject table with CBC subjects."""
#     cbc_subjects = [
#         # Lower Primary (Grade 1-3)
#         {"name": "Mathematics", "code": "MATH", "lessons_per_week": 5, "color_code": "#FF5733", "max_consecutive_periods": 2, "grade_level": "Grade 1-3"},
#         {"name": "English", "code": "ENG", "lessons_per_week": 5, "color_code": "#33C1FF", "max_consecutive_periods": 2, "grade_level": "Grade 1-3"},
#         {"name": "Kiswahili", "code": "KIS", "lessons_per_week": 5, "color_code": "#3396FF", "max_consecutive_periods": 2, "grade_level": "Grade 1-3"},
#         {"name": "Environmental Activities", "code": "ENV", "lessons_per_week": 4, "color_code": "#75FF33", "max_consecutive_periods": 2, "grade_level": "Grade 1-3"},
#         {"name": "Movement and Creative Arts", "code": "ART", "lessons_per_week": 3, "color_code": "#FFB733", "max_consecutive_periods": 2, "grade_level": "Grade 1-3"},
#         # Upper Primary (Grade 4-6)
#         {"name": "Mathematics", "code": "MATH", "lessons_per_week": 5, "color_code": "#FF5733", "max_consecutive_periods": 2, "grade_level": "Grade 4-6"},
#         {"name": "English", "code": "ENG", "lessons_per_week": 5, "color_code": "#33C1FF", "max_consecutive_periods": 2, "grade_level": "Grade 4-6"},
#         {"name": "Kiswahili", "code": "KIS", "lessons_per_week": 5, "color_code": "#3396FF", "max_consecutive_periods": 2, "grade_level": "Grade 4-6"},
#         {"name": "Science and Technology", "code": "SCI", "lessons_per_week": 4, "color_code": "#75FF33", "max_consecutive_periods": 2, "grade_level": "Grade 4-6"},
#         {"name": "Social Studies", "code": "SOC", "lessons_per_week": 3, "color_code": "#FFC133", "max_consecutive_periods": 2, "grade_level": "Grade 4-6"},
#         {"name": "Religious Education", "code": "REL", "lessons_per_week": 2, "color_code": "#9933FF", "max_consecutive_periods": 1, "grade_level": "Grade 4-6"},
#         # Junior Secondary (Grade 7-9)
#         {"name": "Mathematics", "code": "MATH", "lessons_per_week": 6, "color_code": "#FF5733", "max_consecutive_periods": 2, "grade_level": "Grade 7-9"},
#         {"name": "English", "code": "ENG", "lessons_per_week": 5, "color_code": "#33C1FF", "max_consecutive_periods": 2, "grade_level": "Grade 7-9"},
#         {"name": "Kiswahili", "code": "KIS", "lessons_per_week": 5, "color_code": "#3396FF", "max_consecutive_periods": 2, "grade_level": "Grade 7-9"},
#         {"name": "Integrated Science", "code": "SCI", "lessons_per_week": 4, "color_code": "#75FF33", "max_consecutive_periods": 2, "grade_level": "Grade 7-9"},
#         {"name": "Social Studies", "code": "SOC", "lessons_per_week": 3, "color_code": "#FFC133", "max_consecutive_periods": 2, "grade_level": "Grade 7-9"},
#         {"name": "Computer Science", "code": "COMP", "lessons_per_week": 2, "color_code": "#3399FF", "max_consecutive_periods": 2, "grade_level": "Grade 7-9"},
#     ]

#     try:
#         for subject in cbc_subjects:
#             # Check if the subject already exists to prevent duplication
#             existing_subject = CurriculumSubject.query.filter_by(code=subject["code"], grade_level=subject["grade_level"]).first()
#             if not existing_subject:
#                 new_subject = CurriculumSubject(
#                     name=subject["name"],
#                     code=subject["code"],
#                     lessons_per_week=subject["lessons_per_week"],
#                     color_code=subject["color_code"],
#                     max_consecutive_periods=subject["max_consecutive_periods"],
#                     =subject[""],
#                     school_id=current_user.school_id
#                 )
#                 db.session.add(new_subject)

#         db.session.commit()
#         flash('Curriculum subjects added successfully.', 'success')
#     except Exception as e:
#         db.session.rollback()
#         flash(f"Failed to add curriculum subjects: {str(e)}", 'danger')

#     return redirect(url_for('admin.manage_subjects'))


# @bp.route('/curriculum_subject', methods=["GET"])
# @login_required
# @admin_required
# def manage_curriculumsubjects():
#     subjects = CurriculumSubject.query.filter_by(school_id=current_user.school_id).all()
#     return render_template('admin/manage_subjects.html', subjects=subjects)

