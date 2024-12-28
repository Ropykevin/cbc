from typing import Dict, List, Set, Tuple
import random
from app.models.curriculum import CurriculumSubject, GradeLevelSubject
from app.models.teacher import Teacher
from app.utils.timetable_validator import TimetableValidator

class TimetableOptimizer:
    def __init__(self, school_id: int, grade_level: int):
        self.school_id = school_id
        self.grade_level = grade_level
        self.validator = TimetableValidator(school_id)
        self.max_attempts = 100

    def optimize_schedule(self, initial_schedule: Dict[Tuple[int, int], Dict]) -> Dict[Tuple[int, int], Dict]:
        """Optimize the timetable to minimize conflicts and violations"""
        best_schedule = initial_schedule.copy()
        best_score = self._evaluate_schedule(best_schedule)
        
        for _ in range(self.max_attempts):
            new_schedule = self._apply_random_swap(best_schedule.copy())
            new_score = self._evaluate_schedule(new_schedule)
            
            if new_score < best_score:
                best_schedule = new_schedule
                best_score = new_score
                
            if best_score == 0:  # Perfect schedule found
                break
        
        return best_schedule

    def _evaluate_schedule(self, schedule: Dict[Tuple[int, int], Dict]) -> int:
        """Calculate penalty score for a schedule based on constraint violations"""
        score = 0
        
        # Check teacher conflicts
        teacher_conflicts = self.validator.check_teacher_conflicts(schedule)
        score += len(teacher_conflicts) * 100  # High penalty for teacher conflicts
        
        # Check subject distribution
        subject_reqs = self._get_subject_requirements()
        distribution_violations = self.validator.validate_subject_distribution(
            schedule, subject_reqs)
        score += len(distribution_violations) * 50
        
        # Check consecutive subjects
        consecutive_violations = self.validator.check_consecutive_subjects(schedule)
        score += len(consecutive_violations) * 30
        
        # Check teacher workload
        workload_violations = self.validator.validate_teacher_workload(schedule)
        score += len(workload_violations) * 40
        
        return score

    def _apply_random_swap(self, schedule: Dict[Tuple[int, int], Dict]) -> Dict[Tuple[int, int], Dict]:
        """Randomly swap two time slots in the schedule"""
        slots = list(schedule.keys())
        if len(slots) < 2:
            return schedule
            
        slot1, slot2 = random.sample(slots, 2)
        schedule[slot1], schedule[slot2] = schedule[slot2], schedule[slot1]
        
        return schedule

    def _get_subject_requirements(self) -> Dict[int, int]:
        """Get weekly hour requirements for each subject"""
        requirements = {}
        subjects = GradeLevelSubject.query.filter_by(
            school_id=self.school_id,
            grade_level=self.grade_level
        ).all()
        
        for subject in subjects:
            requirements[subject.subject_id] = subject.lessons_per_week
            
        return requirements