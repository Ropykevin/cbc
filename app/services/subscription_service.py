from datetime import datetime, timedelta
from typing import Dict, Optional
from app.extensions import db
from app.models.subscription import SubscriptionTier
from app.models.subscription_feature import SubscriptionFeature
from app.models.school import School

class SubscriptionService:
    @staticmethod
    def get_subscription_tiers() -> Dict:
        """Get all subscription tiers with features"""
        tiers = SubscriptionTier.query.all()
        return {tier.name: {
            'price': tier.price,
            'max_teachers': tier.max_teachers,
            'max_students': tier.max_students,
            'features': [f.name for f in tier.features]
        } for tier in tiers}

    @staticmethod
    def upgrade_subscription(school_id: int, tier_name: str) -> bool:
        """Upgrade school's subscription tier"""
        school = School.query.get_or_404(school_id)
        tier = SubscriptionTier.query.filter_by(name=tier_name).first()
        
        if not tier:
            raise ValueError(f"Invalid subscription tier: {tier_name}")
            
        school.subscription_type = tier_name
        db.session.commit()
        return True

    @staticmethod
    def initialize_subscription_tiers():
        """Initialize default subscription tiers and features"""
        if SubscriptionTier.query.first():
            return

        tiers = {
            'basic': {
                'price': 0,
                'max_teachers': 5,
                'max_students': 150,
                'features': [
                    'Basic timetable generation',
                    'Up to 5 teachers',
                    'Email support'
                ]
            },
            'standard': {
                'price': 99,
                'max_teachers': 15,
                'max_students': 450,
                'features': [
                    'Advanced timetable generation',
                    'Up to 15 teachers',
                    'Priority email support',
                    'Export to PDF/Excel',
                    'Basic analytics'
                ]
            },
            'premium': {
                'price': 199,
                'max_teachers': float('inf'),
                'max_students': float('inf'),
                'features': [
                    'AI-powered timetable optimization',
                    'Unlimited teachers',
                    'Priority 24/7 support',
                    'Advanced analytics',
                    'API access',
                    'Custom branding'
                ]
            }
        }

        for name, data in tiers.items():
            tier = SubscriptionTier(
                name=name,
                price=data['price'],
                max_teachers=data['max_teachers'],
                max_students=data['max_students']
            )
            db.session.add(tier)
            db.session.flush()

            for feature in data['features']:
                feature_obj = SubscriptionFeature(
                    tier_id=tier.id,
                    name=feature,
                    is_active=True
                )
                db.session.add(feature_obj)

        db.session.commit()