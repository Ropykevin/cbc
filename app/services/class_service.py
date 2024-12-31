from typing import Dict, List
from app.extensions import db
from app.models.class_config import ClassConfig
from app.models.teacher import Teacher
import re

class ClassService:
    @staticmethod
    def validate_class_name(name: str) -> bool:
        """Validate class name format (e.g., '4B', '5Red')"""
        pattern = r'^[4-9][A-Za-z]+$'
        return bool(re.match(pattern, name))

    @staticmethod
    def create_class(school_id: int, data: Dict) -> ClassConfig:
        """Create a new class configuration"""
        # Extract grade and division from class name
        grade = int(data['name'][0])
        division = data['name'][1:]

        class_config = ClassConfig(
            school_id=school_id,
            grade_level=grade,
            division=division,
            academic_year=data['academic_year'],
            capacity=data.get('capacity', 30),
            homeroom_teacher_id=data.get('homeroom_teacher_id')
        )

        db.session.add(class_config)
        db.session.commit()
        return class_config

    @staticmethod
    def get_class_timetable(class_id: int) -> List[Dict]:
        """Get formatted timetable for a class"""
        entries = TimetableEntry.query.filter_by(class_id=class_id)\
            .order_by(TimetableEntry.day, TimetableEntry.period).all()
        
        timetable = []
        for entry in entries:
            timetable.append({
                'day': entry.day,
                'period': entry.period,
                'subject': entry.subject.name,
                'teacher': entry.teacher.full_name,
                'time_slot': entry.period_config.get_time_range()
            })
        
        return timetable