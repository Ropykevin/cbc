from datetime import datetime, timedelta
from typing import Dict, List
from app.extensions import db
from app.models.billing import BillingInfo, BillingHistory
from app.models.subscription import SubscriptionTier

class BillingService:
    @staticmethod
    def create_billing_info(school_id: int, data: Dict) -> BillingInfo:
        """Create or update billing information"""
        billing_info = BillingInfo.query.filter_by(school_id=school_id).first()
        if not billing_info:
            billing_info = BillingInfo(school_id=school_id)

        billing_info.billing_email = data['billing_email']
        billing_info.billing_address = data['billing_address']
        billing_info.payment_method = data['payment_method']
        billing_info.last_four = data.get('last_four')
        billing_info.is_annual = data.get('is_annual', False)
        
        # Set next billing date
        billing_info.next_billing_date = datetime.utcnow() + timedelta(
            days=365 if billing_info.is_annual else 30
        )

        db.session.add(billing_info)
        db.session.commit()
        return billing_info

    @staticmethod
    def record_payment(school_id: int, amount: float, status: str, 
                      transaction_id: str = None) -> BillingHistory:
        """Record a payment in billing history"""
        history = BillingHistory(
            school_id=school_id,
            amount=amount,
            status=status,
            transaction_id=transaction_id,
            description=f"Subscription payment - {datetime.utcnow().strftime('%B %Y')}"
        )
        db.session.add(history)
        db.session.commit()
        return history

    @staticmethod
    def get_billing_history(school_id: int) -> List[Dict]:
        """Get billing history for a school"""
        history = BillingHistory.query.filter_by(
            school_id=school_id
        ).order_by(
            BillingHistory.billing_date.desc()
        ).all()
        
        return [{
            'date': entry.billing_date,
            'amount': entry.amount,
            'status': entry.status,
            'description': entry.description
        } for entry in history]