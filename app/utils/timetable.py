from app.models.timetable import TimetableEntry, Subject
from typing import List, Dict
from datetime import datetime

def check_timetable_conflicts(entries: List[TimetableEntry]) -> List[Dict]:
    conflicts = []
    for i, entry1 in enumerate(entries):
        for entry2 in entries[i+1:]:
            if entry1.day == entry2.day and entry1.period == entry2.period:
                if entry1.teacher_id == entry2.teacher_id:
                    conflicts.append({
                        'type': 'teacher',
                        'day': entry1.day,
                        'period': entry1.period,
                        'teacher_id': entry1.teacher_id
                    })
                if entry1.class_id == entry2.class_id:
                    conflicts.append({
                        'type': 'class',
                        'day': entry1.day,
                        'period': entry1.period,
                        'class_id': entry1.class_id
                    })
    return conflicts

def validate_teacher_hours(subject: Subject) -> bool:
    """Validate if teacher has enough available hours"""
    current_assignments = TimetableEntry.query.filter_by(
        teacher_id=subject.teacher_id
    ).count()
    return current_assignments < 30  # Maximum 30 periods per week