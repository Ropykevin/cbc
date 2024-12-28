from typing import List, Dict
from sqlalchemy import func
from app.models.timetable import TimetableEntry, Subject
from app.models.teacher import Teacher

def generate_teacher_workload_report(school_id: int) -> List[Dict]:
    """Generate a report of teacher workloads"""
    return db.session.query(
        User.username,
        Teacher.teacher_code,
        func.count(TimetableEntry.id).label('total_hours')
    ).join(Teacher, User.id == Teacher.user_id
    ).outerjoin(TimetableEntry, Teacher.id == TimetableEntry.teacher_id
    ).filter(User.school_id == school_id
    ).group_by(User.username, Teacher.teacher_code
    ).order_by(func.count(TimetableEntry.id).desc()
    ).all()

def find_unassigned_subjects(school_id: int) -> List[Dict]:
    """Find subjects without teacher assignments"""
    return Subject.query.filter(
        Subject.school_id == school_id,
        ~Subject.id.in_(
            db.session.query(TeacherSubject.subject_id)
        )
    ).all()

def analyze_timetable_gaps(class_id: int) -> List[Dict]:
    """Find gaps in class timetables"""
    gaps = []
    entries = TimetableEntry.query.filter_by(class_id=class_id).all()
    
    for day in range(5):  # Monday to Friday
        day_entries = sorted(
            [e for e in entries if e.day == day],
            key=lambda x: x.period
        )
        
        for i in range(len(day_entries) - 1):
            if day_entries[i+1].period - day_entries[i].period > 1:
                gaps.append({
                    'day': day,
                    'start_period': day_entries[i].period,
                    'end_period': day_entries[i+1].period,
                    'gap_size': day_entries[i+1].period - day_entries[i].period - 1
                })
    
    return gaps