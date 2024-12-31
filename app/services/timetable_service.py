from typing import Dict, List, Optional
from app.models.timetable import TimetableEntry
from app.models.period_config import PeriodConfig
from app.utils.timetable_generator import TimetableGenerator
from app.utils.timetable_validator import TimetableValidator
from app.extensions import db

class TimetableService:
    def __init__(self, school_id: int):
        self.school_id = school_id
        self.generator = TimetableGenerator(school_id)
        self.validator = TimetableValidator()

    def generate_class_timetable(self, class_id: int) -> Optional[Dict]:
        """Generate timetable for a specific class"""
        try:
            # Get period configuration
            periods = PeriodConfig.query.filter_by(
                school_id=self.school_id
            ).order_by(PeriodConfig.period_number).all()
            
            if not periods:
                raise ValueError("No period configuration found")

            # Generate timetable
            timetable = self.generator.generate(class_id, periods)
            if not timetable:
                return None

            # Validate timetable
            if not self._validate_timetable(timetable):
                return None

            # Save timetable
            self._save_timetable(class_id, timetable)
            
            return timetable

        except Exception as e:
            db.session.rollback()
            raise

    def _validate_timetable(self, timetable: Dict) -> bool:
        """Validate generated timetable"""
        return (
            self.validator.validate_distribution(timetable) and
            self.validator.validate_teacher_workload(timetable)
        )

    def _save_timetable(self, class_id: int, timetable: Dict) -> None:
        """Save generated timetable to database"""
        # Clear existing entries
        TimetableEntry.query.filter_by(class_id=class_id).delete()

        # Create new entries
        for (day, period), data in timetable.items():
            entry = TimetableEntry(
                class_id=class_id,
                day=day,
                period=period,
                subject_id=data['subject_id'],
                teacher_id=data['teacher_id']
            )
            db.session.add(entry)

        db.session.commit()