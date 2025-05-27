from datetime import datetime, timedelta
from typing import Dict, Optional
from app.extensions import db
from app.models.subscription import SubscriptionTier
from app.models.subscription import SubscriptionFeature
from app.models.school import School
from app.models.subscription import SubscriptionPackage, SubscriptionTransaction
from app.services.mpesa_service import MpesaService

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

    @staticmethod
    def get_packages():
        """Get all available subscription packages"""
        return SubscriptionPackage.query.all()

    @staticmethod
    def initiate_payment(user_id: int, package_id: int, phone_number: str) -> dict:
        """Initiate subscription payment"""
        try:
            package = SubscriptionPackage.query.get_or_404(package_id)
            
            # Create pending transaction
            transaction = SubscriptionTransaction(
                user_id=user_id,
                package_id=package_id,
                amount=package.price,
                payment_method='mpesa',
                status='pending'
            )
            db.session.add(transaction)
            db.session.flush()
            
            # Initiate M-PESA payment
            reference = f"SUB{transaction.id}"
            payment = MpesaService.initiate_stk_push(
                phone_number=phone_number,
                amount=package.price,
                reference=reference
            )
            
            if payment['success']:
                transaction.transaction_id = payment['checkout_id']
                db.session.commit()
                return {'success': True, 'checkout_id': payment['checkout_id']}
            
            db.session.rollback()
            return {'success': False, 'message': payment['message']}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}

    @staticmethod
    def complete_subscription(checkout_id: str) -> dict:
        """Complete subscription after successful payment"""
        try:
            # Verify payment
            payment = MpesaService.verify_transaction(checkout_id)
            if not payment['success']:
                return payment
            
            # Update transaction
            transaction = SubscriptionTransaction.query.filter_by(
                transaction_id=checkout_id
            ).first()
            
            if not transaction:
                return {'success': False, 'message': 'Transaction not found'}
            
            package = SubscriptionPackage.query.get(transaction.package_id)
            
            transaction.status = 'completed'
            transaction.payment_date = datetime.utcnow()
            transaction.start_date = datetime.utcnow()
            transaction.end_date = datetime.utcnow() + timedelta(days=30 * package.duration_months)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Subscription activated successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}