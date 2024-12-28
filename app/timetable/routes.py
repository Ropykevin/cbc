from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.timetable import bp
from app.models.timetable import Class, TimetableEntry
from app.models.curriculum import CurriculumSubject
from app.utils.timetable_generator import TimetableGenerator
from app.utils.security import admin_required, premium_required
from app.extensions import db

@bp.route('/view/<int:class_id>')
@login_required
def view_timetable(class_id):
    class_obj = Class.query.get_or_404(class_id)
    if class_obj.school_id != current_user.school_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    entries = TimetableEntry.query.filter_by(class_id=class_id).all()
    timetable_data = {}
    for entry in entries:
        timetable_data[(entry.day, entry.period)] = entry
    
    return render_template('timetable/view.html',
                         class_name=class_obj.name,
                         class_id=class_id,
                         entries=timetable_data)

@bp.route('/generate/<int:class_id>', methods=['POST'])
@login_required
@admin_required
@premium_required
def generate_timetable(class_id):
    class_obj = Class.query.get_or_404(class_id)
    if class_obj.school_id != current_user.school_id:
        return jsonify({'error': 'Access denied'}), 403
    
    generator = TimetableGenerator(current_user.school_id, class_obj.grade_level)
    timetable = generator.generate_class_timetable(class_id)
    
    if timetable is None:
        return jsonify({'error': 'Could not generate valid timetable'}), 400
    
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
            db.session.add(entry)
        
        db.session.commit()
        return jsonify({'message': 'Timetable generated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500