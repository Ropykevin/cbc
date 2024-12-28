from typing import Dict, List, Set, Tuple
from app.models.curriculum import CurriculumSubject, TeacherSubject
from app.models.teacher import Teacher

class TimetableValidator:
    def __init__(self, school_id: int):
        self.school_id = school_id
        self.max_periods_per_day = 8
        self.days_per_week = 5

    def check_teacher_conflicts(self, schedule: Dict[Tuple[int, int], Dict]) -> List[Dict]:
        """Check for teacher double-booking"""
        conflicts = []
        teacher_slots = {}
        
        for (day, period), data in schedule.items():
            teacher_id = data['teacher_id']
            if teacher_id not in teacher_slots:
                teacher_slots[teacher_id] = set()
            
            time_slot = (day, period)
            if time_slot in teacher_slots[teacher_id]:
                conflicts.append({
                    'type': 'teacher_conflict',
                    'teacher_id': teacher_id,
                    'day': day,
                    'period': period
                })
            teacher_slots[teacher_id].add(time_slot)
        
        return conflicts

    def validate_subject_distribution(self, schedule: Dict[Tuple[int, int], Dict],
                                   subject_requirements: Dict[int, int]) -> List[Dict]:
        """Validate if subjects meet their weekly hour requirements"""
        subject_counts = {}
        for data in schedule.values():
            subject_id = data['subject_id']
            subject_counts[subject_id] = subject_counts.get(subject_id, 0) + 1
        
        violations = []
        for subject_id, required_hours in subject_requirements.items():
            actual_hours = subject_counts.get(subject_id, 0)
            if actual_hours != required_hours:
                violations.append({
                    'type': 'hours_mismatch',
                    'subject_id': subject_id,
                    'required': required_hours,
                    'actual': actual_hours
                })
        
        return violations

    def check_consecutive_subjects(self, schedule: Dict[Tuple[int, int], Dict]) -> List[Dict]:
        """Check for violation of maximum consecutive periods for subjects"""
        violations = []
        
        for day in range(self.days_per_week):
            current_subject = None
            consecutive_count = 0
            
            for period in range(self.max_periods_per_day):
                entry = schedule.get((day, period))
                if entry:
                    subject_id = entry['subject_id']
                    if subject_id == current_subject:
                        consecutive_count += 1
                        subject = Subject.query.get(subject_id)
                        if consecutive_count > subject.max_consecutive_periods:
                            violations.append({
                                'type': 'consecutive_violation',
                                'subject_id': subject_id,
                                'day': day,
                                'count': consecutive_count
                            })
                    else:
                        current_subject = subject_id
                        consecutive_count = 1
                else:
                    current_subject = None
                    consecutive_count = 0
        
        return violations

    def validate_teacher_workload(self, schedule: Dict[Tuple[int, int], Dict]) -> List[Dict]:
        """Validate teacher workload against their maximum hours"""
        teacher_hours = {}
        for data in schedule.values():
            teacher_id = data['teacher_id']
            teacher_hours[teacher_id] = teacher_hours.get(teacher_id, 0) + 1
        
        violations = []
        for teacher_id, hours in teacher_hours.items():
            teacher = Teacher.query.get(teacher_id)
            if hours > teacher.max_hours_per_week:
                violations.append({
                    'type': 'workload_exceeded',
                    'teacher_id': teacher_id,
                    'max_hours': teacher.max_hours_per_week,
                    'assigned_hours': hours
                })
        
        return violations