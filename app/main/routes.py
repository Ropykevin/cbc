from flask import render_template, redirect, url_for
from flask_login import current_user, login_required
from app.main import bp

@bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.teacher_timetable'))
    return render_template('Landingpage/index.html', title='Welcome')

@bp.route('/teacher/timetable')
@login_required
def teacher_timetable():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('main/teacher_timetable.html')