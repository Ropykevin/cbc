from typing import Dict
from app.extensions import db
from app.models.school import School
from app.models.school_profile import SchoolProfile
from app.models.academic_calendar import AcademicCalendar
from app.models.period_config import PeriodConfig
from datetime import time

class SchoolService:
    @staticmethod
    def create_school(data: Dict) -> School:
        """Create a new school with profile and default configurations"""
        school = School(
            name=data['name'],
            email=data['email'],
            subscription_type='basic'
        )
        db.session.add(school)
        db.session.flush()

        # Create school profile
        profile = SchoolProfile(
            school_id=school.id,
            address=data['address'],
            phone=data['phone'],
            website=data.get('website'),
            logo_url=data.get('logo_url')
        )
        db.session.add(profile)

        # Create academic calendar
        calendar = AcademicCalendar(
            school_id=school.id,
            year=data['academic_year'],
            term_start=data['term_start'],
            term_end=data['term_end']
        )
        db.session.add(calendar)

        # Create default period configuration
        SchoolService._create_default_periods(school.id)

        db.session.commit()
        return school

    @staticmethod
    def _create_default_periods(school_id: int) -> None:
        """Create default period configuration for school"""
        periods = [
            (1, '08:00', '08:45', False),
            (2, '08:45', '09:30', False),
            (3, '09:30', '09:45', True, 15),  # Morning break
            (4, '09:45', '10:30', False),
            (5, '10:30', '11:15', False),
            (6, '11:15', '12:00', False),
            (7, '12:00', '12:45', True, 45),  # Lunch break
            (8, '12:45', '13:30', False)
        ]

        for period_data in periods:
            period = PeriodConfig(
                school_id=school_id,
                period_number=period_data[0],
                start_time=time.fromisoformat(period_data[1]),
                end_time=time.fromisoformat(period_data[2]),
                is_break=period_data[3],
                break_duration=period_data[4] if len(period_data) > 4 else None
            )
            db.session.add(period)