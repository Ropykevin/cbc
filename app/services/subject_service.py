from typing import Dict, List
from app.extensions import db
from app.models.subject_config import SubjectConfig
from app.models.teacher_specialization import TeacherSpecialization

class SubjectService:
    @staticmethod
    def create_subject(school_id: int, data: Dict) -> SubjectConfig:
        """Create a new subject configuration"""
        subject = SubjectConfig(
            school_id=school_id,
            code=data['code'],
            name=data['name'],
            weekly_hours=data['weekly_hours'],
            grade_level=data['grade_level'],
            requires_lab=data.get('requires_lab', False),
            prerequisites=data.get('prerequisites', [])
        )
        
        db.session.add(subject)
        db.session.commit()
        return subject

    @staticmethod
    def assign_teacher(subject_id: int, teacher_id: int, is_primary: bool = False) -> None:
        """Assign a teacher to a subject"""
        # Check if teacher is already assigned
        existing = TeacherSpecialization.query.filter_by(
            subject_id=subject_id,
            teacher_id=teacher_id
        ).first()
        
        if existing:
            raise ValueError("Teacher is already assigned to this subject")

        specialization = TeacherSpecialization(
            subject_id=subject_id,
            teacher_id=teacher_id,
            is_primary=is_primary
        )
        
        db.session.add(specialization)
        db.session.commit()

    @staticmethod
    def remove_teacher(subject_id: int, teacher_id: int) -> None:
        """Remove a teacher from a subject"""
        TeacherSpecialization.query.filter_by(
            subject_id=subject_id,
            teacher_id=teacher_id
        ).delete()
        
        db.session.commit()