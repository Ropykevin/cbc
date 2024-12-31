from typing import Dict, List
from app.extensions import db
from app.models.teacher import Teacher
from app.models.teacher_profile import TeacherProfile
from app.models.teacher_specialization import TeacherSpecialization
from app.utils.validators import validate_phone_number

class TeacherService:
    @staticmethod
    def create_teacher(school_id: int, data: Dict) -> Teacher:
        """Create a new teacher with profile and specializations"""
        if not validate_phone_number(data['phone']):
            raise ValueError("Invalid phone number format")

        teacher = Teacher(school_id=school_id)
        db.session.add(teacher)
        db.session.flush()

        profile = TeacherProfile(
            teacher_id=teacher.id,
            title=data['title'],
            employee_id=data['employee_id'],
            phone=data['phone'],
            emergency_contact=data['emergency_contact'],
            emergency_contact_name=data['emergency_contact_name'],
            max_hours_per_week=data['max_hours_per_week'],
            preferred_grade_levels=data['preferred_grade_levels'],
            preferred_time_slots=data['preferred_time_slots']
        )
        db.session.add(profile)

        for subject_id in data['specializations']:
            spec = TeacherSpecialization(
                teacher_id=teacher.id,
                subject_id=subject_id,
                is_primary=subject_id == data['primary_subject_id']
            )
            db.session.add(spec)

        db.session.commit()
        return teacher

    @staticmethod
    def update_teacher(teacher_id: int, data: Dict) -> Teacher:
        """Update teacher profile and specializations"""
        teacher = Teacher.query.get_or_404(teacher_id)
        profile = teacher.profile

        if 'phone' in data and not validate_phone_number(data['phone']):
            raise ValueError("Invalid phone number format")

        # Update profile fields
        for field in ['title', 'phone', 'emergency_contact', 
                     'emergency_contact_name', 'max_hours_per_week']:
            if field in data:
                setattr(profile, field, data[field])

        # Update specializations
        if 'specializations' in data:
            # Remove old specializations
            TeacherSpecialization.query.filter_by(teacher_id=teacher.id).delete()
            
            # Add new specializations
            for subject_id in data['specializations']:
                spec = TeacherSpecialization(
                    teacher_id=teacher.id,
                    subject_id=subject_id,
                    is_primary=subject_id == data.get('primary_subject_id')
                )
                db.session.add(spec)

        db.session.commit()
        return teacher