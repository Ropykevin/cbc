from typing import Dict, List, Optional, Tuple
from app.models.curriculum import GradeLevelSubject, TeacherSubject
from app.models.teacher import Teacher
from app.utils.timetable_validator import TimetableValidator
from app.utils.timetable_optimizer import TimetableOptimizer

class TimetableGenerator:
    def __init__(self, school_id: int, grade_level: int):
        self.school_id = school_id
        self.grade_level = grade_level
        self.validator = TimetableValidator(school_id)
        self.optimizer = TimetableOptimizer(school_id, grade_level)
        self.max_periods = 8
        self.days = 5

    def generate_class_timetable(self, class_id: int) -> Optional[Dict[Tuple[int, int], Dict]]:
        """Generate a complete timetable for a class"""
        # Get subject requirements
        subjects = self._get_subject_requirements()
        if not subjects:
            return None
            
        # Generate initial schedule
        initial_schedule = self._create_initial_schedule(subjects)
        if not initial_schedule:
            return None
            
        # Optimize the schedule
        optimized_schedule = self.optimizer.optimize_schedule(initial_schedule)
        
        # Validate final schedule
        if self._is_valid_schedule(optimized_schedule):
            return optimized_schedule
            
        return None

    def _get_subject_requirements(self) -> List[Dict]:
        """Get all required subjects with their teachers"""
        subjects = []
        grade_subjects = GradeLevelSubject.query.filter_by(
            school_id=self.school_id,
            grade_level=self.grade_level
        ).all()
        
        for gs in grade_subjects:
            teacher_subjects = TeacherSubject.query.filter_by(
                subject_id=gs.subject_id
            ).all()
            
            if teacher_subjects:  # Only include subjects with assigned teachers
                subjects.append({
                    'subject_id': gs.subject_id,
                    'lessons_per_week': gs.lessons_per_week,
                    'teachers': [ts.teacher_id for ts in teacher_subjects]
                })
                
        return subjects

    def _create_initial_schedule(self, subjects: List[Dict]) -> Dict[Tuple[int, int], Dict]:
        """Create an initial schedule placing subjects randomly"""
        schedule = {}
        available_slots = [(d, p) for d in range(self.days) 
                          for p in range(self.max_periods)]
        
        for subject in subjects:
            remaining_lessons = subject['lessons_per_week']
            while remaining_lessons > 0 and available_slots:
                slot = self._find_suitable_slot(schedule, subject, available_slots)
                if slot:
                    available_slots.remove(slot)
                    schedule[slot] = {
                        'subject_id': subject['subject_id'],
                        'teacher_id': self._assign_teacher(subject['teachers'], slot,
                                                         schedule)
                    }
                    remaining_lessons -= 1
                else:
                    break
                    
        return schedule if len(schedule) == len(available_slots) else None

    def _find_suitable_slot(self, schedule: Dict[Tuple[int, int], Dict],
                          subject: Dict, available_slots: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Find a suitable time slot for a subject"""
        import random
        random.shuffle(available_slots)
        
        for slot in available_slots:
            temp_schedule = schedule.copy()
            temp_schedule[slot] = {
                'subject_id': subject['subject_id'],
                'teacher_id': subject['teachers'][0]  # Temporary assignment
            }
            
            if not self.validator.check_consecutive_subjects(temp_schedule):
                return slot
                
        return None

    def _assign_teacher(self, teachers: List[int], slot: Tuple[int, int],
                       schedule: Dict[Tuple[int, int], Dict]) -> int:
        """Assign the most suitable teacher for a time slot"""
        for teacher_id in teachers:
            conflicts = False
            for (day, period), data in schedule.items():
                if data['teacher_id'] == teacher_id and day == slot[0]:
                    if abs(period - slot[1]) < 2:  # Avoid consecutive periods
                        conflicts = True
                        break
            
            if not conflicts:
                return teacher_id
                
        return teachers[0]  # Fallback to first teacher if no better option found

    def _is_valid_schedule(self, schedule: Dict[Tuple[int, int], Dict]) -> bool:
        """Validate the complete schedule"""
        return not (self.validator.check_teacher_conflicts(schedule) or
                   self.validator.check_consecutive_subjects(schedule) or
                   self.validator.validate_teacher_workload(schedule))